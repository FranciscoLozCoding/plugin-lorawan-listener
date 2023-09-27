import json
import logging
import re
import datetime
from dateutil import parser

def parse_message_payload(payload_data):

    tmp_dict = json.loads(payload_data)

    return tmp_dict

def Get_Measurement_metadata(message_dict):
    tmp_dict = {}

    #Get static metadata
    tmp_dict['devAddr'] = message_dict.get('devAddr', None)

    #get values from nested dictionary
    deviceInfo_dict = message_dict.get('deviceInfo', None)
    try:
        tmp_dict['tenantId'] = deviceInfo_dict['tenantId']
        tmp_dict['tenantName'] = deviceInfo_dict['tenantName']
        tmp_dict['applicationId'] = deviceInfo_dict['applicationId']
        tmp_dict['applicationName'] = deviceInfo_dict['applicationName']
        tmp_dict['deviceProfileId'] = deviceInfo_dict['deviceProfileId']
        tmp_dict['deviceProfileName'] = deviceInfo_dict['deviceProfileName']
        tmp_dict['deviceName'] = deviceInfo_dict['deviceName']
        tmp_dict['devEui'] = deviceInfo_dict['devEui']
    except:
        logging.error("deviceInfo was not found")
        raise ValueError("deviceInfo was not found")

    #get tags
    tags_dict = deviceInfo_dict.get('tags', None)
    try:
        for key, value in tags_dict.items():
            tmp_dict[key + "_tag"] = value
    except:
        pass

    return tmp_dict

def clean_message_measurement(measurement):

    #pattern excepted 
    pattern = r'[^a-z0-9_]'

    #replace not excepted values with '_' in measurement["name"]
    measurement["name"] = re.sub(pattern, '_', measurement["name"])

    return measurement

def Get_Signal_Performance_values(message_dict):
    tmp_dict = {}

    #Get Lorawan Performance values
    tmp_dict['rxInfo'] = []
    try:
        for val in message_dict['rxInfo']:
            temp = {"gatewayId":val['gatewayId'],"rssi":val['rssi'],"snr":val['snr']}
            tmp_dict['rxInfo'].append(temp)
    except:
        logging.error("rxInfo was not found")
        raise ValueError("rxInfo was not found")

    txInfo_dict = message_dict.get('txInfo', None)
    try:
        tmp_dict['spreadingFactor'] = txInfo_dict['modulation']["lora"]["spreadingFactor"]
    except:
        logging.error("spreadingFactor was not found")
        raise ValueError("spreadingFactor was not found")

    return tmp_dict

def Get_Signal_Performance_metadata(message_dict):
    tmp_dict = {}

    #get values from nested dictionary
    deviceInfo_dict = message_dict.get('deviceInfo', None)
    try:
        tmp_dict['deviceName'] = deviceInfo_dict['deviceName']
        tmp_dict['devEui'] = deviceInfo_dict['devEui']
    except:
        logging.error("deviceInfo was not found")
        raise ValueError("deviceInfo was not found")

    #get tags
    tags_dict = deviceInfo_dict.get('tags', None)
    try:
        for key, value in tags_dict.items():
            tmp_dict[key + "_tag"] = value
    except:
        pass

    return tmp_dict


def convert_time(iso_time):
    # Parse the timestamp string using dateutil.parser
    try:
        datetime_obj = parser.isoparse(iso_time)
    except ValueError as e:
        print(f"Error: {e}")
    else:
        # Convert the datetime object to nanoseconds since the epoch
        total_seconds = datetime_obj.timestamp()
        nanoseconds = int(total_seconds * 1e9)

    return nanoseconds
