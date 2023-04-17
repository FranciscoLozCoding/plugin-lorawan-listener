import argparse
import logging
import os

import paho.mqtt.client as mqtt
from Message import on_message_publish
from Message import on_message_dry

def main():

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
        default=os.getenv("MQTT_SERVER_HOST", "127.0.0.1"),
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
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    client = mqtt.Client("lorawan-test")
    logging.info(f"connecting [{args.mqtt_server_ip}:{args.mqtt_server_port}]...")
    client.connect(host=args.mqtt_server_ip, port=args.mqtt_server_port, bind_address="0.0.0.0")
    logging.info(f"subscribing [{args.mqtt_subscribe_topic}]...")
    client.subscribe(args.mqtt_subscribe_topic)
    logging.info("waiting for callback...")
    client.on_message = on_message_dry if args.dry else on_message_publish
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
