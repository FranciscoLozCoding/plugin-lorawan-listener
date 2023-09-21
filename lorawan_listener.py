import argparse
import logging
import os
import paho.mqtt.client as mqtt
from Message import on_message_publish
from Message import on_message_dry
from Callbacks import *

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
        "--measurements",
        nargs="*",  # 0 or more values expected => creates a list
        type=str,
        default=[],  # default if nothing is provided
        help="A list of chirpstack measurement names to publish. If empty all will be published (ex: --measurements m1 m2 m3)"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    #configure client and connection
    client = mqtt.Client("lorawan-listener")
    logging.info(f"connecting [{args.mqtt_server_ip}:{args.mqtt_server_port}]...")
    client.connect(host=args.mqtt_server_ip, port=args.mqtt_server_port, bind_address="0.0.0.0")
    client.on_connect = on_connect
    logging.info(f"subscribing [{args.mqtt_subscribe_topic}]...")
    client.subscribe(args.mqtt_subscribe_topic)
    client.on_subscribe = on_subscribe
    logging.info("waiting for callback...")
    client.on_message = on_message_dry if args.dry else lambda client, userdata, message: on_message_publish(client, userdata, message, args.measurements)
    #enable reconnection: 
    # delay is the number of seconds to wait between successive reconnect attempts(default=1).
    # delay_max is the maximum number of seconds to wait between reconnection attempts(default=1)
    client.reconnect_delay_set(min_delay=5, max_delay=60)
    client.on_log = on_log #prints if args.debug = true
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
