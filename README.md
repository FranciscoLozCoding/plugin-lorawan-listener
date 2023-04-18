# LoRaWAN Listener Plugin Usage Instructions

## About The Plugin

This plugin is designed to handle the configuration of the backend MQTT (Message Queuing Telemetry Transport) to receive data from LoRaWAN (Long Range Wide Area Network) devices. Essentially, it sets up a way for the LoRaWAN devices to send data to a central location, where it can be used by other applications.

When the plugin receives data from a LoRaWAN device, it publishes that data to the beehive. This is where all the data received from the LoRaWAN devices is stored. Other users can then subscribe to this measurment called *lorawan.data* to access the data, or use it to build larger applications that rely on LoRaWAN data.

To help users identify where the data came from, the plugin includes metadata when it publishes the data to the beehive. This metadata includes information about which specific LoRaWAN device sent the data, or other details that can help users understand the context in which the data was collected.

## Prerequisites

Before the plugin can work...
1) Rpi with RAK concentrator has to be discoverable by K3s Cluster
1) [WES access to the RAK concentrator has to be enabled](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#enabling-wes-access-to-the-rak-concentrator)
1) [LoRa End Device is activated via OTAA](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#configuring-the-wes-lorawan)

>TODO: add link to waggle lorawan repo to first step to new section about setting up RAK Discover Kit 2

>For more information see [Waggle-lorawan](https://github.com/waggle-sensor/waggle-lorawan)

## Running waggle-listener

### Arguments

**--debug**: enable debug logs

**--dry**: enable dry-run mode where no messages will be broadcast to Beehive

**--mqtt-server-ip**: MQTT server IP address

**--mqtt-server-port**: MQTT server port

**--mqtt-subscribe-topic**: MQTT subscribe topic

## Retrieving Published Data

### Subcribing To Plugin

### Querying Data

## Consumer Example





# Additional Information

## Metadata

## Accessing LoRa End Device

>TODO: maybe add this section to Waggle-lorawan instead of this plugin repo

## Setting up RAK Discover Kit 2 to be discoverable by WES


>TODO: maybe add this section to Waggle-lorawan instead of this plugin repo


## Learn More & Supporting Documentation

- [LoRa-E5 AT Command Specification](https://files.seeedstudio.com/products/317990687/res/LoRa-E5%20AT%20Command%20Specification_V1.0%20.pdf)
- [RAK2287 Quick Start Guide](https://docs.rakwireless.com/Product-Categories/WisLink/RAK2287/Quickstart/)
- [Summer 2022 Student Research](https://github.com/waggle-sensor/summer2022/blob/main/Tsai/Documentation.md)
- [Waggle-lorawan](https://github.com/waggle-sensor/waggle-lorawan)
- [Wes-Chirpstack](https://github.com/waggle-sensor/waggle-edge-stack/tree/main/kubernetes/wes-chirpstack)
- [Chirpstack Documentation](https://www.chirpstack.io/docs/index.html)
- [Minicom Documentation](https://linux.die.net/man/1/minicom)