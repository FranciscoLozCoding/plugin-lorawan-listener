"""
Loriot inbox watcher.

Watches a directory for new files (one Loriot JSON message per file), parses them
with parse_loriot_payload and publishes via the shared pipeline. No direct WebSocket
connection (plugin netpol does not allow outbound). Use scripts/loriot-websocket-to-files.sh
on the node to connect to Loriot and write messages into this directory.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Optional

from parse_loriot import parse_loriot_payload
from client import process_and_publish
from calc import PacketLossCalculator


class LoriotInboxWatcher:
    """
    Watches an inbox directory for Loriot JSON message files, parses and publishes
    each, then deletes the file. Runs the poll loop in a daemon thread.
    """

    def __init__(self, inbox_dir: str, args: Any, contract: Optional[Any] = None) -> None:
        self.inbox_dir = inbox_dir
        self.args = args
        self.contract = contract
        self.plr_calc = PacketLossCalculator(args.plr)
        self.poll_interval_sec = float(getattr(args, "loriot_poll_interval_sec", 1.5))

    def _process_file(self, path: str) -> bool:
        """Read file, parse as Loriot JSON, publish if valid. Returns True if caller should delete the file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                body = f.read()
        except OSError as e:
            logging.warning("Loriot inbox: could not read %s: %s", path, e)
            return True
        try:
            parsed = parse_loriot_payload(
                body,
                codec_contract=self.contract,
            )
        except Exception as e:
            logging.warning("Loriot inbox: parse failed for %s: %s", path, e)
            return True
        if parsed is None:
            logging.debug("Loriot inbox: no measurements in %s; skipping", path)
            return True
        if getattr(self.args, "dry", False):
            logging.info("Loriot inbox message received: %s", path)
            self._log_measurements(parsed["measurements"])
            return True
        try:
            process_and_publish(
                parsed["measurements"],
                parsed["timestamp_ns"],
                parsed["measurement_metadata"],
                parsed["signal_values"],
                parsed["signal_metadata"],
                self.args,
                self.plr_calc,
            )
        except Exception as e:
            logging.exception("Loriot inbox: publish failed for %s: %s", path, e)
            return False
        return True

    def _log_measurements(self, measurements: list) -> None:
        """Log measurement names and values (respecting --ignore and --collect). Used when --dry."""
        for m in measurements:
            if m["name"] in self.args.ignore:
                continue
            if self.args.collect and m["name"] not in self.args.collect:
                continue
            logging.info("%s: %s", m["name"], m["value"])

    def _run_loop(self) -> None:
        """Poll inbox directory for files, process and delete. Runs until thread is stopped."""
        while True:
            try:
                if not os.path.isdir(self.inbox_dir):
                    logging.debug("Loriot inbox: directory %s not present yet", self.inbox_dir)
                    time.sleep(self.poll_interval_sec)
                    continue
                names = os.listdir(self.inbox_dir)
                for name in names:
                    if name.startswith("."):
                        continue
                    path = os.path.join(self.inbox_dir, name)
                    if not os.path.isfile(path):
                        continue
                    if self._process_file(path):
                        try:
                            os.remove(path)
                        except OSError as e:
                            logging.warning("Loriot inbox: could not remove %s: %s", path, e)
            except Exception as e:
                logging.exception("Loriot inbox: poll error: %s", e)
            time.sleep(self.poll_interval_sec)

    def start_daemon(self) -> None:
        """Start the inbox watcher in a daemon thread. Returns immediately."""
        thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="loriot-inbox",
        )
        thread.start()
        logging.info("Loriot inbox watcher started for %s", self.inbox_dir)


def start_loriot_inbox_daemon(
    args: Any, contract: Optional[Any] = None
) -> None:
    """
    Start the Loriot inbox watcher in a daemon thread.

    Call when --loriot-inbox-dir is set. Polls the directory for new files,
    parses each as Loriot JSON, publishes via the shared pipeline, then deletes the file.
    """
    inbox_dir = (getattr(args, "loriot_inbox_dir", None) or "").strip()
    if not inbox_dir:
        return
    watcher = LoriotInboxWatcher(inbox_dir, args, contract)
    watcher.start_daemon()
