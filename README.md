# LoRaWAN Listener Plugin Usage Instructions

## About The Plugin

This plugin is designed to handle the configuration of the backend MQTT (Message Queuing Telemetry Transport) to receive data from LoRaWAN (Long Range Wide Area Network) devices. Essentially, it sets up a way for the LoRaWAN devices to send data to a central location, where it can be used by other applications.

When the plugin receives data from a LoRaWAN device, it publishes that data to the beehive. This is where all the data received from the LoRaWAN devices is stored. Other users can then subscribe to this measurement called *lorawan.data* to access the data, or use it to build larger applications that rely on LoRaWAN data.

To help users identify where the data came from, the plugin includes metadata when it publishes the data to the beehive. This metadata includes information about which specific LoRaWAN device sent the data, or other details that can help users understand the context in which the data was collected.

>IMPORTANT: This plugin currently only works in the US Region due to regulations in radio channels and [wes-chirpstack](https://github.com/waggle-sensor/waggle-edge-stack/tree/main/kubernetes/wes-chirpstack) being set up for US Region.

## Prerequisites

Before the plugin can work...
1) [Rpi with RAK concentrator has to be discoverable by K3s Cluster](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md##setting-up-rak-discover-kit-2-to-be-discoverable-by-wes)
1) [WES access to the RAK concentrator has to be enabled](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#enabling-wes-access-to-the-rak-concentrator)
1) [LoRa End Device is activated via OTAA](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#configuring-the-wes-lorawan)

>For more information see [Waggle-lorawan](https://github.com/waggle-sensor/waggle-lorawan)

To configure any LoRaWan settings such as devices, gateways, and applications the chirpstack Web UI will be used. The Web UI can be accessed by establishing a proxy connection to `wes-chirpstack-server` running on the node. If the proxy connection is established using port `8080`, the web address is http://localhost:8080/. See [Configuring the WES LoraWan](https://github.com/waggle-sensor/waggle-lorawan/blob/main/README.md#configuring-the-wes-lorawan) on how to access the chirpstack Web UI.

## Running lorawan-listener

Once the prerequisites are completed, lorawan-listener can now run on the node. To run lorawan-listener on the node it must be scheduled using the [Edge Scheduler (ES)](https://docs.waggle-edge.ai/docs/about/architecture#edge-scheduler-es). There is a [walkthrough example](https://docs.waggle-edge.ai/docs/tutorials/schedule-jobs) on the Sage website under docs that can be followed. The lorawan-listener plugin can also be scheduled using the [Sage Portal's UI to create jobs](https://portal.sagecontinuum.org/create-job). An example of the job's yaml file is found below.

```
name: Lorawan_TestJob
plugins:
- name: lorawan-listener
  pluginSpec:
    image: registry.sagecontinuum.org/flozano/lorawan-listener:0.0.1
    selector:
      zone: core
nodeTags: []
nodes:
  W030: true
scienceRules:
- 'schedule("lorawan-listener"): cronjob("lorawan-listener", "* * * * *")'
successCriteria:
- WallClock('1day')
```

Once the job is scheduled and the prerequisites are configured correctly, the node will receive data being sent by LoRaWan devices and publish it to the beehive under the measurement called `lorawan.data`.

### Arguments

**--debug**: enable debug logs

**--dry**: enable dry-run mode where no messages will be broadcast to Beehive

**--mqtt-server-ip**: MQTT server IP address

**--mqtt-server-port**: MQTT server port

**--mqtt-subscribe-topic**: MQTT subscribe topic

## Retrieving Published Data

There are two recommended approaches to retrieving `lorawan.data`:

1) Subscribing to lorawan-listener plugin
1) Using the Data API

Each is appropriate for different use cases and integrations, but generally if your building an application that relies on `lorawan.data` then subcribe to the lorawan-listener plugin.

>IMPORTANT: All values published by lorawan-listener plugin is published as data type string.

### Subscribing to lorawan-listener plugin

To subscribe to the lorawan-listener plugin, your plugin must be running on the same node as the lorawan-listener. You can refer to the [Subscribing to other measurements](https://github.com/waggle-sensor/pywaggle/blob/main/docs/writing-a-plugin.md#subscribing-to-other-measurements) resource to learn how to subscribe to measurements. Additionally, you can find an example of a plugin that uses the lorawan-listener plugin in this repository called [plugin-lorawan-example](https://github.com/waggle-sensor/plugin-lorawan-example).

### Using the Data API

To learn how to use the Data API, refer to the [Using the Data API](https://sagecontinuum.org/docs/tutorials/accessing-data#using-the-data-api) resource. This example below shows how to retrieve LoRaWAN data using the HTTP API. Specifically, it retrieves data identified by the "lorawan.data" identifier, which was published by a LoRaWAN device called "Lozano LoRA E5 Mini" in the last 30 days.

```
curl -H 'Content-Type: application/json' https://data.sagecontinuum.org/api/v1/query -d '
{
    "start": "-30d",
    "filter": {
         "name":"lorawan.data",
         "deviceName": "Lozano LoRA E5 Mini"
    }
}'
```

## Additional Information

This section provides you with additional information that will help you when exploring the lorawan-listener plugin.

## Metadata

The examples provided are specific instances of metadata that are only published for the measurement `lorawan.data`.

- "Type_tag": "test device"
- "applicationId": "5b06bc92-0510-47c1-8f24-a807f48b94a9"
- "applicationName": "wes-application"
- "devAddr": "00362614"
- "devEui": "5a3f18b97a97247d"
- "deviceName": "Lozano LoRA E5 Mini"
- "deviceProfileId": "d0c4ec0e-51cc-4654-ab0d-b1b614dd95c5"
- "deviceProfileName": "Wio-E5 Dev Kit for Long Range Application"
- "tenantId": "52f14cd4-c6f1-4fbd-8f87-4025e1d49242"
- "tenantName": "ChirpStack"

Metadata that follows the naming convention "{TagName}_tag" where {TagName} represents the name of the tag, are tags that were added in chirpstack to the device profile. In other words, if a tag named "Unit" was added to the device profile, the metadata related to the "Unit" tag would be named as "Unit_tag". This naming convention allows for easy identification and organization of metadata related to specific device profile tags in the ChirpStack platform.

>NOTE: The metadata that is associated with LoRaWAN data can be utilized to filter the data when subscribing to the plugin or when using the data API. In other words, if you are using a plugin or the data API to access LoRaWAN data, you can use the metadata to filter the data so that you can focus on specific information that is relevant to your needs.

## Recommendations 

When you are setting up your LoRaWAN environment, it is essential to make sure that your devices and the data they collect are easy to identify and organize.

For instance, imagine a large field filled with LoRaWAN devices collecting soil moisture data. It can be challenging to locate a specific device that may be broken or collecting data outliers. Therefore, when setting up your LoRaWAN environment, it is crucial to utilize ChirpStack features that allow you to identify the context in which the data was collected.

There are several ways to achieve this. For example, you can use an organized naming convention when naming your devices in ChirpStack. This can make it simpler to identify specific devices that may require maintenance or troubleshooting. Additionally, you can utilize applications and tags to organize and manage the data collected by your devices.

### Creating Chirpstack Applications
When you are setting up your ChirpStack environment, it is important to make sure that the data collected by your LoRaWAN devices is easy to identify and organize.

One way to achieve this is by creating applications that can be thought of as bins. Each application can be responsible for collecting different measurements such as soil moisture, temperature, humidity, or for different science goals.

In summary, creating applications in your ChirpStack environment that reflect the specific measurements or science goals that your LoRaWAN devices are responsible for can make it simpler to identify, organize, and manage the data that is being collected.

### Using Tags

ChirpStack offers a useful feature that allows you to add tags to device profiles. You can take advantage of this feature to help identify, organize, and manage the data that is being collected by your LoRaWAN devices.

One effective way to use tags is to add a 'Type' tag that can be used to label devices that are in Testing, Maintenance, or Production. By doing so, you can easily differentiate between devices that are in different stages of their life cycle and also have an idea about the quality of data that is being published by the devices.

For example, you can filter devices with a 'Type' tag that is labeled as 'Maintenance' to troubleshoot issues. Similarly, you can filter devices with a 'Type' tag that is labeled as 'Testing' to ensure that data is being collected properly before deploying the device to the production environment.

In summary, adding tags to device profiles in ChirpStack can help you manage and organize your LoRaWAN data. You can use tags such as 'Type' to differentiate between devices and easily identify the quality of data that is being published.

## Learn More & Supporting Documentation

- [LoRa-E5 AT Command Specification](https://files.seeedstudio.com/products/317990687/res/LoRa-E5%20AT%20Command%20Specification_V1.0%20.pdf)
- [RAK2287 Quick Start Guide](https://docs.rakwireless.com/Product-Categories/WisLink/RAK2287/Quickstart/)
- [Summer 2022 Student Research](https://github.com/waggle-sensor/summer2022/blob/main/Tsai/Documentation.md)
- [Waggle-lorawan](https://github.com/waggle-sensor/waggle-lorawan)
- [Wes-Chirpstack](https://github.com/waggle-sensor/waggle-edge-stack/tree/main/kubernetes/wes-chirpstack)
- [Chirpstack Documentation](https://www.chirpstack.io/docs/index.html)
- [Minicom Documentation](https://linux.die.net/man/1/minicom)