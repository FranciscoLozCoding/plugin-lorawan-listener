"""
Loriot WebSocket uplink parser.
Requires decoded payload in 'decoded.data' or legacy 'object'. Rejects messages without decoded payload.
Sets measurement_metadata.lns from WebSocket URL host when provided (e.g. us1.loriot.io).
"""
import json
import logging
from urllib.parse import urlparse

from parse import clean_string


def _lns_from_websocket_url(websocket_url):
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


def _loriot_ts_to_ns(ts_ms):
    """Convert Loriot millisecond timestamp to nanoseconds since epoch."""
    if ts_ms is None:
        return None
    try:
        return int(ts_ms) * 1_000_000
    except (TypeError, ValueError):
        return None


def parse_loriot_payload(body, websocket_url=None, codec_contract=None):
    """
    Parse Loriot uplink JSON. Requires decoded payload in 'decoded.data' or 'object', or
    uses codec fallback when codec_contract is set and decoded is missing.

    Returns dict with keys: measurements, timestamp_ns, measurement_metadata, signal_values, signal_metadata,
    or None if decoded payload is missing and codec fallback is not used or fails.
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

    if measurements is None or not measurements:
        logging.debug("Loriot: no decoded.data/object and codec fallback did not yield measurements; skipping")
        return None

    ts_ms = data.get("ts")
    timestamp_ns = _loriot_ts_to_ns(ts_ms)
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
