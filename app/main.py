"""
LoRaWAN Listener plugin entry point.

Parses CLI and env, configures logging, loads and warms the codec contract (if configured),
then starts the Loriot WebSocket client (if enabled) and the ChirpStack MQTT client.
"""
import logging
import argparse
import os
from codec_loader import Contract
from client import ChirpstackClient
from loriot_client import start_loriot_client_daemon


def main() -> None:
    """Parse arguments, set up logging and codec contract, then run ChirpStack (and optionally Loriot) clients."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument(
        "--dry",
        action="store_true",
        default=False,
        help="enable dry-run mode where no messages will be broadcast to Beehive",
    )
    parser.add_argument(
        "--mqtt-server-ip",
        default=os.getenv("MQTT_SERVER_HOST", "wes-rabbitmq"),
        help="MQTT server IP address",
    )
    parser.add_argument(
        "--mqtt-server-port",
        default=os.getenv("MQTT_SERVER_PORT", "1883"),
        help="MQTT server port",
        type=int,
    )
    parser.add_argument(
        "--mqtt-subscribe-topic",
        default=os.getenv("MQTT_SUBSCRIBE_TOPIC", "application/#"),
        help="MQTT subscribe topic",
    )
    parser.add_argument(
        "--collect",
        nargs="*",  # 0 or more values expected => creates a list
        type=str,
        default=[],  # default if nothing is provided
        help="A list of chirpstack measurements to retrieve. If empty all will be retrieved (ex: --collect m1 m2 m3)"
    )
    parser.add_argument(
        "--ignore",
        nargs="*",  # 0 or more values expected => creates a list
        type=str,
        default=[],  # default if nothing is provided
        help="A list of chirpstack measurements to ignore (opposite of --collect). If empty all will be retrieved (ex: --ignore m1 m2 m3)"
    )
    parser.add_argument(
        "--signal-strength-indicators",
        action="store_true",
        default=False,
        help="enable signal strength indicators"
    )
    parser.add_argument(
        "--plr",
        default=os.getenv("PLR", 3600),
        help="plr's(packet loss rate) time interval in seconds, for example 3600 will mean plr will be measured every hour",
        type=int
    )
    parser.add_argument(
        "--enable-loriot",
        action="store_true",
        default=False,
        help="enable Loriot WebSocket client to receive uplinks from Loriot network server",
    )
    parser.add_argument(
        "--loriot-websocket-url",
        default=os.getenv("LORIOT_WEBSOCKET_URL", ""),
        help="Loriot WebSocket URL (required when --enable-loriot); e.g. wss://...",
    )
    parser.add_argument(
        "--loriot-app-token",
        default=os.getenv("LORIOT_APP_TOKEN", ""),
        help="optional Loriot app token for WebSocket authentication",
    )
    default_cache = os.path.expanduser(
        os.getenv("LORAWAN_CODEC_CACHE", "~/.cache/lorawan-listener-codecs")
    )
    _default_codec_map = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "codec_map.json"
    )
    parser.add_argument(
        "--codec-map",
        default=os.getenv("LORAWAN_CODEC_MAP", _default_codec_map),
        help="codec fallback map: path to JSON file or JSON string (device name/regex -> repo URL or path)",
    )
    parser.add_argument(
        "--codec-cache-dir",
        default=default_cache,
        help="directory to clone GitHub codec repos into (default: LORAWAN_CODEC_CACHE or ~/.cache/lorawan-listener-codecs)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    # Load codec map and warm codec cache before clients start to avoid races.
    codec_map = Contract.load_codec_map(args.codec_map)
    codec_contract = Contract(codec_map, args.codec_cache_dir) if codec_map and args.codec_cache_dir else None
    if codec_contract:
        codec_contract.warm_codec_cache()

    if args.enable_loriot:
        start_loriot_client_daemon(args, codec_contract)

    mqtt_client = ChirpstackClient(args, codec_contract)
    mqtt_client.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
