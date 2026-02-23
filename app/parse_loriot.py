"""
Loriot WebSocket uplink parser.

Parses Loriot uplink JSON. Expects decoded payload in 'decoded.data' or legacy 'object';
if missing, can use codec_contract to decode raw payload. Sets measurement_metadata.lns
from WebSocket URL host when provided (e.g. us1.loriot.io). Returns a normalized dict
for the shared publish pipeline or None if the message cannot be parsed.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import re
from parse import clean_string

def _hide_token(url: str) -> str:
    # Remove or redact token query param from URLs for logging
    # Example: wss://us1.loriot.io/app?token=abcdefg&xyz=123 -> wss://us1.loriot.io/app?token=***&xyz=123
    if not url:
        return url
    # Replace token=... in query with token=***
    return re.sub(r'(\btoken=)[^&]+', r'\1***', url)

def _lns_from_websocket_url(websocket_url: Optional[str]) -> str:
    """Parse host from WebSocket URL for use as lns (e.g. wss://us1.loriot.io/app?token=... -> us1.loriot.io)."""
    if not websocket_url:
        return "loriot"
    try:
        parsed = urlparse(websocket_url)
        if parsed.netloc:
            return parsed.netloc
    except Exception:
        pass
    return "loriot"


def _loriot_ts_to_ns(ts_ms: Optional[Any]) -> Optional[int]:
    """Convert Loriot millisecond timestamp to nanoseconds since epoch."""
    if ts_ms is None:
        return None
    try:
        return int(ts_ms) * 1_000_000
    except (TypeError, ValueError):
        return None


def parse_loriot_payload(
    body: Union[str, Dict[str, Any]],
    websocket_url: Optional[str] = None,
    codec_contract: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """
    Parse Loriot uplink JSON into a normalized payload for the shared pipeline.

    Expects decoded payload in 'decoded.data' or 'object'; if missing, uses
    codec_contract.decode_with_codec when provided. Returns a dict with keys:
    measurements, timestamp_ns, measurement_metadata, signal_values, signal_metadata,
    or None if the message cannot be decoded.
    """
    try:
        data = json.loads(body) if isinstance(body, str) else body
    except (json.JSONDecodeError, TypeError) as e:
        logging.warning("Loriot: invalid JSON: %s", e)
        return None

    decoded = data.get("decoded", {}) or {}
    payload = decoded.get("data") or data.get("object")
    measurements = None

    if payload and isinstance(payload, dict):
        measurements = []
        for key, value in payload.items():
            if value is None:
                continue
            name = clean_string(str(key))
            measurements.append({"name": name, "value": value})
        if not measurements:
            measurements = None

    if measurements is None and codec_contract:
        raw_data = data.get("data")
        device_name = data.get("name")
        if raw_data is not None and device_name:
            measurements = codec_contract.decode_with_codec(
                device_name, raw_data, encoding="hex"
            )

    if not measurements:
        logging.debug("Loriot: no decoded.data/object and codec fallback did not yield measurements; skipping")
        return None

    timestamp_ns = _loriot_ts_to_ns(data.get("ts"))
    if timestamp_ns is None:
        logging.debug("Loriot: no ts; skipping")
        return None

    lns = _lns_from_websocket_url(websocket_url)
    device_name = data.get("name")
    eui = data.get("EUI")

    measurement_metadata = {
        "lns": lns,
        "deviceName": device_name,
        "devEui": eui,
    }

    # Do not publish signal measurements for Loriot (rssi, snr, pl, plr, etc.)
    #TODO: This will be done in a later version of the plugin.
    signal_values = None
    signal_metadata = None

    return {
        "measurements": measurements,
        "timestamp_ns": timestamp_ns,
        "measurement_metadata": measurement_metadata,
        "signal_values": signal_values,
        "signal_metadata": signal_metadata,
    }
