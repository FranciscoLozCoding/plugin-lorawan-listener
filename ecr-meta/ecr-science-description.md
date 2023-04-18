# About The Plugin

This plugin is designed to handle the configuration of the backend MQTT (Message Queuing Telemetry Transport) to receive data from LoRaWAN (Long Range Wide Area Network) devices. Essentially, it sets up a way for the LoRaWAN devices to send data to a central location, where it can be used by other applications.

When the plugin receives data from a LoRaWAN device, it publishes that data to the beehive. This is where all the data received from the LoRaWAN devices is stored. Other users can then subscribe to this measurment called *lorawan.data* to access the data, or use it to build larger applications that rely on LoRaWAN data.

To help users identify where the data came from, the plugin includes metadata when it publishes the data to the beehive. This metadata includes information about which specific LoRaWAN device sent the data, or other details that can help users understand the context in which the data was collected.

# Using the code

Before the plugin can work...
1) Rpi with RAK concentrator has to be discoverable by K3s Cluster
1) [WES access to the RAK concentrator has to be enabled](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#enabling-wes-access-to-the-rak-concentrator)
1) [LoRa End Device is activated via OTAA](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#configuring-the-wes-lorawan)

>For more information see [Waggle-lorawan](https://github.com/waggle-sensor/waggle-lorawan)

# Arguments

**--debug**: enable debug logs

**--dry**: enable dry-run mode where no messages will be broadcast to Beehive

**--mqtt-server-ip**: MQTT server IP address

**--mqtt-server-port**: MQTT server port

**--mqtt-subscribe-topic**: MQTT subscribe topic