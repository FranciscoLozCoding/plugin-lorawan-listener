## About The Plugin

This plugin is designed to handle the configuration of the backend MQTT (Message Queuing Telemetry Transport) to receive value(s) from LoRaWAN (Long Range Wide Area Network) devices. It can receive data from **both** the local ChirpStack (MQTT) and **Loriot** (WebSocket) at the same time, so you can aggregate local gateway traffic and remote Loriot traffic on one node. Essentially, it sets up a way for the LoRaWAN devices to send data to a central location, where it can be used by other applications.

When the plugin receives data from a LoRaWAN device, it publishes that data to the beehive. This is where all the data received from the LoRaWAN devices is stored. Other users can then subscribe to the measurement(s) to access the data, or use it to build larger applications that rely on LoRaWAN data.

To help users identify where the value came from, the plugin includes metadata when it publishes the value to the beehive. This metadata includes information about which specific LoRaWAN device sent the data, or other details that can help users understand the context in which the value was collected.

If enabled, along with the measurements the plugin will also publish signal strength indicators to help users determine the strength of the wireless connection. The indicators published are as follows with links for more information on the indicator.

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

**--dry**: enable dry-run mode where no messages will be broadcast to Beehive

**--mqtt-server-ip**: MQTT server IP address

**--mqtt-server-port**: MQTT server port

**--mqtt-subscribe-topic**: MQTT subscribe topic

**--collect**: A list of chirpstack measurements to retrieve. If empty all will be retrieved (ex: --collect m1 m2 m3)

**--ignore**: (opposite of --collect) A list of chirpstack measurements to ignore. If empty all will be retrieved (ex: --ignore m1 m2 m3)

**--signal-strength-indicators**: enable signal strength indicators

**--plr**: plr's(packet loss rate) time interval in seconds, for example 3600 will mean plr will be measured every hour

**--enable-loriot**: enable the Loriot WebSocket client to receive uplinks from the Loriot network server (runs alongside ChirpStack)

**--loriot-websocket-url**: Loriot WebSocket URL (required when using --enable-loriot). Can be set via `LORIOT_WEBSOCKET_URL` environment variable.

**--loriot-app-token**: optional Loriot app token for WebSocket authentication. Can be set via `LORIOT_APP_TOKEN` environment variable.

# Loriot Integration

When using Loriot, configure a **Payload Codec (JavaScript formatter)** in the LORIOT console so that WebSocket messages include the decoded **`object`** field. Also, make sure to **enable extended verbosity** in the LORIOT console so that the WebSocket messages can include radio information such as RSSI, SNR, and spreading factor. Finally, enable the **Device Name** option in the LORIOT console so that the WebSocket messages can include the device name.