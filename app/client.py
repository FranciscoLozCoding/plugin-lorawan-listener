"""
ChirpStack MQTT client and shared publish pipeline.

Subscribes to ChirpStack MQTT, parses payloads (with optional codec fallback when object
is missing), and publishes measurements and optional signal metrics via the Waggle plugin.
Supports --dry to log messages without publishing.
"""
from __future__ import annotations

import logging
import os
from typing import Any, List, Dict, Optional

import paho.mqtt.client as mqtt
from waggle.plugin import Plugin
from parse import (
    parse_message_payload,
    convert_time,
    Get_Measurement_metadata,
    Get_Signal_Performance_values,
    Get_Signal_Performance_metadata,
    clean_message_measurement,
)
from calc import PacketLossCalculator


def process_and_publish(
    measurements: List[Dict[str, Any]],
    timestamp_ns: Optional[int],
    measurement_metadata: Dict[str, Any],
    signal_values: Optional[Dict[str, Any]],
    signal_metadata: Optional[Dict[str, Any]],
    args: Any,
    plr_calc: PacketLossCalculator,
) -> None:
    """
    Shared publish pipeline for ChirpStack and Loriot.

    Applies --collect/--ignore, cleans measurement names, publishes each measurement,
    and optionally signal metrics (spreading factor, pl, plr, rssi, snr per gateway).
    """
    for measurement in measurements:
        if measurement["name"] in args.ignore:
            continue
        if args.collect and measurement["name"] not in args.collect:
            continue
        _publish_measurement(measurement, timestamp_ns, measurement_metadata)

    if not args.signal_strength_indicators or not signal_values or not signal_metadata:
        return

    perf = signal_values
    meta = signal_metadata.copy()
    _publish_signal(
        {"name": "signal.spreadingfactor", "value": perf.get("spreadingfactor")},
        timestamp_ns,
        meta,
    )
    pl, plr = plr_calc.process_packet(
        meta["devEui"], perf.get("fCnt")
    )
    _publish_signal({"name": "signal.pl", "value": pl}, timestamp_ns, meta)
    if plr is not None:
        _publish_signal({"name": "signal.plr", "value": plr}, timestamp_ns, meta)
    for val in perf.get("rxInfo") or []:
        meta["gatewayId"] = val.get("gatewayId")
        _publish_signal({"name": "signal.rssi", "value": val.get("rssi")}, timestamp_ns, meta)
        _publish_signal({"name": "signal.snr", "value": val.get("snr")}, timestamp_ns, meta)


def _publish_signal(
    measurement: Dict[str, Any],
    timestamp: Optional[int],
    metadata: Dict[str, Any],
) -> None:
    """Publish a single signal metric (e.g. rssi, snr) to the plugin."""
    _publish(measurement, timestamp, metadata)


def _publish_measurement(
    measurement: Dict[str, Any],
    timestamp: Optional[int],
    metadata: Dict[str, Any],
) -> None:
    """Clean measurement name and publish to the plugin."""
    measurement = clean_message_measurement(measurement.copy())
    _publish(measurement, timestamp, metadata)


def _publish(
    measurement: Dict[str, Any],
    timestamp: Optional[int],
    metadata: Dict[str, Any],
) -> None:
    """Publish one measurement to the Waggle plugin if value is not None."""
    if measurement.get("value") is not None:
        with Plugin() as plugin:
            try:
                plugin.publish(
                    measurement["name"],
                    measurement["value"],
                    timestamp=timestamp,
                    meta=metadata,
                )
                logging.info("%s published", measurement["name"])
            except Exception as e:
                logging.error(
                    "measurement %s did not publish: %s",
                    measurement["name"],
                    str(e),
                )


class ChirpstackClient:
    """MQTT client for ChirpStack. Subscribes to application topics and publishes decoded measurements."""

    def __init__(self, args: Any, contract: Optional[Any] = None) -> None:
        """Build MQTT client and packet-loss calculator. Contract is the codec fallback (optional)."""
        self.args = args
        self.contract = contract
        self.client = self.configure_client()
        self.plr_calc = PacketLossCalculator(self.args.plr)

    def configure_client(self) -> mqtt.Client:
        client_id = self.generate_client_id()
        client = mqtt.Client(client_id)
        client.on_subscribe = self.on_subscribe
        client.on_connect = self.on_connect
        #reconnect_delay_set: 
        # delay is the number of seconds to wait between successive reconnect attempts(default=1).
        # delay_max is the maximum number of seconds to wait between reconnection attempts(default=1)
        client.reconnect_delay_set(min_delay=5, max_delay=60)
        if self.args.dry:
            client.on_message = lambda client, userdata, message: self.dry_message(client, userdata, message)
        else:
            client.on_message = lambda client, userdata, message: self.publish_message(client, userdata, message)
        client.on_log = self.on_log
        return client

    @staticmethod
    def generate_client_id() -> str:
        """Return a unique MQTT client id from hostname and PID."""
        hostname = os.uname().nodename
        process_id = os.getpid()
        return f"{hostname}-{process_id}"

    def on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, rc: int) -> None:
        if rc == 0:
            logging.info("Connected to MQTT broker")
            client.subscribe(self.args.mqtt_subscribe_topic)
        else:
            logging.error(f"Connection to MQTT broker failed with code {rc}") 
        return

    @staticmethod
    def on_subscribe(
        client: mqtt.Client, obj: Any, mid: int, granted_qos: Any
    ) -> None:
        logging.info("Subscribed: %s %s", mid, granted_qos)
        return

    @staticmethod
    def on_log(client: mqtt.Client, obj: Any, level: Any, string: str) -> None:
        logging.debug(string)
        return

    def publish_message(
        self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        self.log_message(message)

        try:
            metadata = parse_message_payload(message.payload.decode("utf-8"))
        except Exception:
            logging.error("Message payload could not be parsed.")
            return

        measurements = None
        try:
            measurements = metadata["object"]["measurements"]
        except (KeyError, TypeError):
            pass

        if measurements is None and self.contract:
            raw_data = metadata.get("data")
            device_info = metadata.get("deviceInfo") or {}
            device_name = device_info.get("deviceName")
            if raw_data is not None and device_name:
                measurements = self.contract.decode_with_codec(
                    device_name, raw_data, encoding="base64"
                )

        if measurements is None:
            logging.error("ChirpStack message did not contain measurements and codec fallback did not apply.")
            return

        timestamp_ns = convert_time(metadata.get("time"))
        if timestamp_ns is None:
            logging.error("ChirpStack message missing or invalid time: %s", metadata.get("time"))
            return
        try:
            measurement_metadata = Get_Measurement_metadata(metadata)
        except Exception:
            return

        signal_values = Get_Signal_Performance_values(metadata) if self.args.signal_strength_indicators else None
        signal_metadata = Get_Signal_Performance_metadata(metadata) if self.args.signal_strength_indicators else None

        process_and_publish(
            measurements,
            timestamp_ns,
            measurement_metadata,
            signal_values,
            signal_metadata,
            self.args,
            self.plr_calc,
        )

    def dry_message(
        self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage
    ) -> None:
        """Log raw message and measurements without publishing (used when --dry)."""
        self.log_message(message)
        self.log_measurements(message)

    @staticmethod
    def log_message(message: mqtt.MQTTMessage) -> None:
        """Log raw ChirpStack MQTT message payload and topic."""
        logging.info(
            "LORAWAN Message received: %s with topic %s",
            message.payload.decode("utf-8"),
            message.topic,
        )

    def log_measurements(self, message: mqtt.MQTTMessage) -> None:

        try: #get metadata and measurements received
            metadata = parse_message_payload(message.payload.decode("utf-8"))
            measurements = metadata["object"]["measurements"]
        except:
            logging.error("Message did not contain measurements.")
            return

        if self.args.signal_strength_indicators:
            Performance_vals = Get_Signal_Performance_values(metadata)
            Performance_metadata = Get_Signal_Performance_metadata(metadata)
        
        for measurement in measurements:
            # Skip the measurement if it's in the ignore list
            if measurement["name"] in self.args.ignore:
                continue
            if self.args.collect: #true if not empty
                if measurement["name"] in self.args.collect: #if not empty only log measurements in list
                    logging.info(str(measurement["name"]) + ": " + str(measurement["value"]))
            else: #else collect is empty so log all measurements
                    logging.info(str(measurement["name"]) + ": " + str(measurement["value"]))

        if self.args.signal_strength_indicators:
            for val in Performance_vals['rxInfo']:
                logging.info("gatewayId: " + str(val["gatewayId"]))
                logging.info("  rssi: " + str(val["rssi"]))
                logging.info("  snr: " + str(val["snr"]))
            logging.info("spreading factor: " + str(Performance_vals["spreadingfactor"]))
            pl,plr = self.plr_calc.process_packet(Performance_metadata['devEui'], Performance_vals['fCnt'])
            logging.info(f"packet loss: {pl}")
            if plr is not None:
                logging.info(f"packet loss rate: {plr:.2f}%")

        return

    def run(self) -> None:
        """Connect to MQTT broker and run the event loop (blocks until disconnect)."""
        logging.info(f"connecting [{self.args.mqtt_server_ip}:{self.args.mqtt_server_port}]...")
        self.client.connect(host=self.args.mqtt_server_ip, port=self.args.mqtt_server_port, bind_address="0.0.0.0")
        logging.info("waiting for callback...")
        self.client.loop_forever()
