"""
Loriot uplink parser.

Parses Loriot uplink JSON (e.g. from file or WebSocket). Expects decoded payload in
'decoded.data' or legacy 'object'; if missing, can use codec_contract to decode raw
payload. Sets measurement_metadata.lns to "loriot" (Loriot is decoupled from the
listener; messages may come from files). Returns a normalized dict for the shared
publish pipeline or None if the message cannot be parsed.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Union

from parse import clean_string

LORIOT_LNS = "loriot"

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

    device_name = data.get("name")
    eui = data.get("EUI")
    devaddr = data.get("devaddr")

    measurement_metadata = {
        "lns": LORIOT_LNS,
        "deviceName": device_name,
        "devEui": eui,
        "devAddr": devaddr,
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
