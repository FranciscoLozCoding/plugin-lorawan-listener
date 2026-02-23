## About The Plugin

This plugin is designed to handle the configuration of the backend MQTT (Message Queuing Telemetry Transport) to receive value(s) from LoRaWAN (Long Range Wide Area Network) devices. It can receive data from **both** the local ChirpStack (MQTT) and **Loriot** (via file inbox) at the same time, so you can aggregate local gateway traffic and remote Loriot traffic on one node. Essentially, it sets up a way for the LoRaWAN devices to send data to a central location, where it can be used by other applications.

When the plugin receives data from a LoRaWAN device, it publishes that data to the beehive. This is where all the data received from the LoRaWAN devices is stored. Other users can then subscribe to the measurement(s) to access the data, or use it to build larger applications that rely on LoRaWAN data.

To help users identify where the value came from, the plugin includes metadata when it publishes the value to the beehive. This metadata includes information about which specific LoRaWAN device sent the data, or other details that can help users understand the context in which the value was collected.

When using **ChirpStack** with `--signal-strength-indicators`, the plugin publishes signal strength indicators. **Loriot** uplinks do not include signal metrics (RSSI, SNR, PL, PLR). The indicators for ChirpStack are:

- [RSSI](https://www.thethingsnetwork.org/docs/lorawan/rssi-and-snr/#rssi)
- [SNR](https://www.thethingsnetwork.org/docs/lorawan/rssi-and-snr/#snr)
- [Spreading Factor](https://www.thethingsnetwork.org/docs/lorawan/spreading-factors/)
- **PL** (packet loss): The number of data packets lost during transmission from the LoRaWAN end device to the network server.
- **PLR** (packet loss ratio): The ratio of the number of data packets lost during transmission to the total number of packets sent or expected over a specific period, expressed as a percentage. It quantifies the reliability of communication between LoRaWAN end devices and the network server.

The plugin expects the payload in the following format:
```
payload = {
  measurements:[
  {name:"measurement_name",value:measurement_value},
  {name:"measurement_name",value:measurement_value}, ...
  ]
}
```

>IMPORTANT: This plugin currently only works in the US Region due to regulations in radio channels and [wes-chirpstack](https://github.com/waggle-sensor/waggle-edge-stack/tree/main/kubernetes/wes-chirpstack) being set up for US Region.

# Using the code

Before the plugin can work...
1) The node must have a healthy LoRaWAN gateway
1) [The Payload Conforms with LoRaWAN Listener](https://github.com/FranciscoLozCoding/plugin-lorawan-listener#converting-chirpstack-payload-decoders)

For more information see [Waggle-lorawan](https://github.com/waggle-sensor/waggle-lorawan)

# Arguments

**--debug**: enable debug logs

**--dry**: enable dry-run mode where no messages will be broadcast to Beehive (applies to both ChirpStack and Loriot)

**--mqtt-server-ip**: MQTT server IP address

**--mqtt-server-port**: MQTT server port

**--mqtt-subscribe-topic**: MQTT subscribe topic

**--collect**: A list of chirpstack measurements to retrieve. If empty all will be retrieved (ex: --collect m1 m2 m3)

**--ignore**: (opposite of --collect) A list of chirpstack measurements to ignore. If empty all will be retrieved (ex: --ignore m1 m2 m3)

**--signal-strength-indicators**: enable signal strength indicators

**--plr**: plr's(packet loss rate) time interval in seconds, for example 3600 will mean plr will be measured every hour

**--loriot-inbox-dir**: directory to watch for Loriot message files. Plugin does not connect to Loriot; run `scripts/loriot-websocket-to-files.sh` on the node to write messages here. Env: `LORAWAN_LORIOT_INBOX` or `LORIOT_INBOX_DIR`.

**--codec-map**: codec fallback map (path to a JSON file or a string containing JSON). Used when Loriot messages lack `decoded` or ChirpStack messages lack `object.measurements`. Map keys are device names or regex patterns; values are GitHub repo URLs or local paths to a directory containing `codec.py`. To host multiple codecs in one repo, append a path after `.git` (e.g. `https://github.com/org/codec.git/codecs/water`). Can be set via `LORAWAN_CODEC_MAP` environment variable.

**--codec-cache-dir**: directory where GitHub codec repos are cloned (default: `~/.cache/lorawan-listener-codecs`). Can be set via `LORAWAN_CODEC_CACHE` environment variable.

# Codec fallback

When a message has no decoded payload (Loriot: missing or empty `decoded`; ChirpStack: missing `object` or `object.measurements`), the plugin can decode the raw payload using a device-mapped Python codec if `--codec-map` is set. The map is a JSON object: keys are device names or regex patterns (first match wins), values are GitHub repo URLs or local paths. The codec source must contain a `codec.py` at the repo root (or in a path after `.git`) with a class `Codec` and a method `decode(self, payload_bytes: bytes) -> dict` that returns a flat dict of measurement name → value. The plugin converts that to the internal measurements format. See the README **Codec fallback** section and the **examples/codec_example/** directory in plugin's repo for the example codec and map.

# Loriot Integration

Loriot input is via **file inbox** only (plugin does not connect to Loriot). Set `--loriot-inbox-dir` to a path that is mounted into the plugin pod; run `scripts/loriot-websocket-to-files.sh` on the node with `LORIOT_WEBSOCKET_URL` and `LORIOT_INBOX_DIR` (or `LORAWAN_LORIOT_INBOX`) set. **LNS metadata**: ChirpStack uses `lns: "local_chirpstack"`; Loriot uses `lns: "loriot"`. Codec fallback and Device Name in LORIOT apply as in the README. The plugin does **not** publish signal indicators for Loriot.