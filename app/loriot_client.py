"""
Loriot WebSocket client. Connects to Loriot, receives uplinks, and publishes via the shared pipeline.
Requires Payload Codec in LORIOT console so messages include decoded payload in 'decoded.data' (see Loriot Uplink Data Message docs).
"""
import logging
import threading
import time
from parse_loriot import parse_loriot_payload
from client import process_and_publish
from calc import PacketLossCalculator
import websocket


class LoriotClient:
    """WebSocket client for Loriot uplinks. Runs in a thread and publishes via the shared pipeline."""

    def __init__(self, args, contract=None):
        self.args = args
        self.contract = contract
        self.plr_calc = PacketLossCalculator(args.plr)
        self._url = getattr(args, "loriot_websocket_url", None) or ""
        self._token = getattr(args, "loriot_app_token", None) or ""

    def _on_message(self, ws, message):
        logging.debug("Loriot WebSocket message: %s", message)
        try:
            if getattr(self.args, "dry", False):
                self.dry_message(ws, message)
                return
            parsed = parse_loriot_payload(
                message,
                self._url,
                codec_contract=self.contract,
            )
            if parsed is None:
                return
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
            logging.exception("Loriot message handling failed: %s", e)

    def dry_message(self, ws, message):
        """Log raw message and decoded measurements without publishing (when --dry)."""
        self.log_message(message)
        self.log_measurements(message)

    @staticmethod
    def log_message(message):
        """Log raw Loriot WebSocket message."""
        logging.info("Loriot WebSocket message received: %s", message)

    def log_measurements(self, message):
        """Parse Loriot message and log measurements (respecting --ignore and --collect)."""
        try:
            parsed = parse_loriot_payload(
                message,
                self._url,
                codec_contract=self.contract,
            )
        except Exception as e:
            logging.error("Loriot message could not be parsed: %s", e)
            return
        if parsed is None:
            logging.error("Loriot message did not contain measurements.")
            return
        measurements = parsed["measurements"]
        for m in measurements:
            if m["name"] in self.args.ignore:
                continue
            if self.args.collect and m["name"] not in self.args.collect:
                continue
            logging.info("%s: %s", m["name"], m["value"])

    def _on_error(self, ws, error):
        logging.warning("Loriot WebSocket error: %s", error)

    def _on_close(self, ws, close_status_code, close_msg):
        logging.info("Loriot WebSocket closed: %s %s", close_status_code, close_msg)

    def _run_loop(self):
        """Connect to Loriot WebSocket and process messages. Reconnects with backoff on disconnect."""
        delay = 1
        max_delay = 60

        while True:
            try:
                header = [f"Authorization: Bearer {self._token}"] if self._token else None
                ws = websocket.WebSocketApp(
                    self._url,
                    header=header,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                logging.info("Loriot WebSocket connecting to %s", self._url)
                ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                logging.warning("Loriot WebSocket error: %s", e)
            delay = min(delay * 2, max_delay)
            logging.info("Loriot WebSocket reconnecting in %s s", delay)
            time.sleep(delay)

    def start_daemon(self):
        """Start the WebSocket client in a daemon thread."""
        thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="loriot-ws",
        )
        thread.start()
        logging.info("Loriot WebSocket client started in background thread.")


def start_loriot_client_daemon(args, contract=None):
    """
    Start the Loriot WebSocket client in a daemon thread.
    Call this when --enable-loriot is set and --loriot-websocket-url is provided.
    """
    if not getattr(args, "enable_loriot", False):
        return
    url = getattr(args, "loriot_websocket_url", None) or ""
    if not url:
        logging.warning("Loriot enabled but --loriot-websocket-url not set; skipping Loriot client.")
        return

    client = LoriotClient(args, contract)
    client.start_daemon()
