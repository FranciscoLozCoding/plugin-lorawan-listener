"""
Codec fallback: device-mapped Python codecs from a JSON map (file path or JSON string).

When Loriot lacks decoded.data or ChirpStack lacks object.measurements, the plugin can
decode raw payload using a Codec class loaded from a GitHub repo or local path. Map keys
are device names or regex patterns; values are repo URLs or paths (path after .git for
multiple codecs in one repo). The Contract class holds the map and cache dir and
provides warm_codec_cache() and decode_with_codec().
"""
from __future__ import annotations

import base64
import importlib.util
import json
import logging
import os
import re
import subprocess
import threading
from typing import Any, Dict, List, Optional, Tuple

from parse import clean_string

# Lock for clone/import to avoid races when Loriot and ChirpStack use codecs from same repo.
_clone_import_lock = threading.Lock()

# Cache: codec_dir -> Codec instance (shared across Contract instances)
_codec_instance_cache = {}
_cache_lock = threading.Lock()


def _resolve_entry_for_device(
    device_name: str, codec_map: Dict[str, str]
) -> Optional[str]:
    """Return url_or_path for the first matching key (exact or regex), or None if no match."""
    if not codec_map or not device_name:
        return None
    if device_name in codec_map:
        return codec_map[device_name]
    for key, url_or_path in codec_map.items():
        try:
            if re.match(key, device_name):
                return url_or_path
        except re.error:
            continue
    return None


def _is_github_url(url_or_path: Any) -> bool:
    return isinstance(url_or_path, str) and (
        url_or_path.startswith("http://") or url_or_path.startswith("https://")
    )


def _sanitize_cache_key(url: str) -> str:
    """Derive a safe directory name from a GitHub URL."""
    s = url.strip().rstrip("/")
    for prefix in ("https://github.com/", "http://github.com/"):
        if s.startswith(prefix):
            s = s[len(prefix) :]
            break
    return re.sub(r"[^a-zA-Z0-9._-]", "_", s)


def _ensure_repo_cloned(url: str, cache_dir: str) -> Optional[str]:
    """Clone repo into cache_dir if not present; return path to repo root. Thread-safe."""
    key = _sanitize_cache_key(url)
    dest = os.path.join(cache_dir, key)
    with _clone_import_lock:
        if os.path.isdir(dest):
            try:
                subprocess.run(
                    ["git", "pull"],
                    cwd=dest,
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                pass
            return dest
        try:
            os.makedirs(cache_dir, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--depth", "1", url, dest],
                check=True,
                capture_output=True,
                timeout=60,
            )
            return dest
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logging.warning("Git clone failed for %s: %s", url, e)
            return None


def _load_codec_from_path(codec_dir: str) -> Optional[Any]:
    """Load Codec class from codec_dir/codec.py. Returns Codec instance or None. Thread-safe."""
    codec_py = os.path.join(codec_dir, "codec.py")
    if not os.path.isfile(codec_py):
        logging.warning("codec.py not found in %s", codec_dir)
        return None
    with _cache_lock:
        if codec_dir in _codec_instance_cache:
            return _codec_instance_cache[codec_dir]
    with _clone_import_lock:
        spec = importlib.util.spec_from_file_location("codec", codec_py)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "Codec"):
            logging.warning("Codec class not found in %s", codec_py)
            return None
        instance = mod.Codec()
        with _cache_lock:
            _codec_instance_cache[codec_dir] = instance
        return instance


def _split_base_subpath(value: str) -> Tuple[str, Optional[str]]:
    """
    Split map value into (clone_url_or_path, subpath). Allows one repo to host multiple codecs.
    Format: anything after .git is the path to the codec directory.
    Example: https://github.com/waggle-sensor/codec.git/codecs/water -> clone .../codec.git, codec at repo_root/codecs/water.
    If no '.git' in value, subpath is None (codec.py at root).
    """
    if not value or ".git" not in value:
        return value, None
    i = value.index(".git") + 4
    base = value[:i].strip()
    subpath = value[i:].strip().strip("/") or None
    return base, subpath


def _resolve_codec_dir(url_or_path: str, cache_dir: str) -> Optional[str]:
    """
    Resolve map value to directory that contains codec.py. Returns path or None.
    If value contains .git, the part after .git is the path to the codec (e.g. .../codec.git/codecs/water).
    """
    if not url_or_path or not isinstance(url_or_path, str):
        return None
    base, subpath = _split_base_subpath(url_or_path)
    if not base:
        return None
    if _is_github_url(base):
        repo_dir = _ensure_repo_cloned(base, cache_dir)
        if repo_dir is None:
            return None
        if subpath:
            codec_dir = os.path.join(repo_dir, subpath)
            return codec_dir if os.path.isdir(codec_dir) else None
        return repo_dir
    path = os.path.abspath(os.path.expanduser(base))
    if subpath:
        path = os.path.join(path, subpath)
    return path if os.path.isdir(path) else None


class Contract:
    """
    Codec fallback contract: holds codec map and cache dir, and provides
    warm_codec_cache() and decode_with_codec() for device-mapped decoding.
    """

    @staticmethod
    def load_codec_map(value: str) -> Optional[Dict[str, str]]:
        """
        Parse --codec-map value into a dict (pattern_or_name -> url_or_path).
        If value.strip().startswith('{'), parse as JSON string; else treat as path to JSON file.
        Returns dict or None if empty/invalid.
        """
        if not value or not isinstance(value, str):
            return None
        raw = value.strip()
        if not raw:
            return None
        try:
            if raw.startswith("{"):
                return json.loads(raw)
            with open(raw, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning("Codec map load failed: %s", e)
            return None

    def __init__(self, codec_map: Dict[str, str], cache_dir: str) -> None:
        """Hold codec map and cache dir; _resolved_dirs and _codec_instances are filled on use."""
        self.codec_map = codec_map
        self.cache_dir = cache_dir
        self._resolved_dirs = {}  # url_or_path -> codec_dir
        self._codec_instances = {}  # codec_dir -> Codec instance

    def warm_codec_cache(self) -> None:
        """
        Load all codec.py classes for entries in the map so clones/imports happen before
        clients start, avoiding races. Call from main before starting Loriot or MQTT client.
        """
        if not self.codec_map or not self.cache_dir:
            return
        seen = set()
        for url_or_path in self.codec_map.values():
            if not url_or_path or url_or_path in seen:
                continue
            seen.add(url_or_path)
            try:
                if url_or_path not in self._resolved_dirs:
                    self._resolved_dirs[url_or_path] = _resolve_codec_dir(url_or_path, self.cache_dir)
                codec_dir = self._resolved_dirs[url_or_path]
                if codec_dir and codec_dir not in self._codec_instances:
                    instance = _load_codec_from_path(codec_dir)
                    if instance is not None:
                        self._codec_instances[codec_dir] = instance
            except Exception as e:
                logging.warning("Codec warm-up failed for %s: %s", url_or_path, e)

    def decode_with_codec(
        self,
        device_name: str,
        payload: str,
        encoding: str = "hex",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Decode raw payload using device-mapped codec.

        Returns list of {"name": str, "value": Any} or None. payload is hex (Loriot)
        or base64 (ChirpStack) string; encoding must be "hex" or "base64".
        """
        if not self.codec_map or not self.cache_dir or not device_name or payload is None:
            logging.debug("Codec Contract: no codec map or cache dir or device name or payload")
            return None
        url_or_path = _resolve_entry_for_device(device_name, self.codec_map)
        if url_or_path is None:
            logging.debug("Codec Contract: no matching codec map entry for device name %s", device_name)
            return None
        if url_or_path not in self._resolved_dirs:
            logging.debug("Codec Contract: url_or_path not in cache, resolving codec directory for url_or_path %s", url_or_path)
            self._resolved_dirs[url_or_path] = _resolve_codec_dir(url_or_path, self.cache_dir)
        codec_dir = self._resolved_dirs[url_or_path]
        if codec_dir is None:
            logging.debug("Codec Contract: no codec directory for url_or_path %s", url_or_path)
            return None
        if codec_dir not in self._codec_instances:
            logging.debug("Codec Contract: codec_dir not in cache, loading codec from path %s", codec_dir)
            instance = _load_codec_from_path(codec_dir)
            if instance is not None:
                self._codec_instances[codec_dir] = instance
        codec_instance = self._codec_instances.get(codec_dir)
        if codec_instance is None:
            logging.debug("Codec Contract: no codec instance for codec_dir %s", codec_dir)
            return None
        try:
            if encoding == "hex":
                payload_bytes = bytes.fromhex(payload)
            elif encoding == "base64":
                payload_bytes = base64.b64decode(payload)
            else:
                logging.warning("Codec Contract: unknown payload encoding: %s", encoding)
                return None
        except Exception as e:
            logging.warning("Codec Contract: payload decode failed: %s", e)
            return None
        try:
            result = codec_instance.decode(payload_bytes)
        except Exception as e:
            logging.warning("Codec Contract: codec decode failed: %s", e)
            return None
        if not isinstance(result, dict):
            logging.debug("Codec Contract: codec decode did not return a dict")
            return None
        measurements = []
        for key, value in result.items():
            if value is None:
                continue
            name = clean_string(str(key))
            measurements.append({"name": name, "value": value})
        logging.debug("Codec Contract: decoded measurements: %s", measurements)
        return measurements if measurements else None
