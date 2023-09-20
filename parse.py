import json
import logging
import re
import time

def parse_message_payload(payload_data):

    tmp_dict = json.loads(payload_data)

    return tmp_dict

def clean_message_dict(message_dict):
    tmp_dict = {}

    #Get static metadata
    tmp_dict['devAddr'] = message_dict.pop('devAddr', None)

    #get values from nested dictionary
    deviceInfo_dict = message_dict.pop('deviceInfo', None)
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
    tags_dict = deviceInfo_dict.pop('tags', None)
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

def convert_time(iso_time):
    # Convert the timestamp string into a struct_time object
    struct_time = time.strptime(iso_time, '%Y-%m-%dT%H:%M:%S.%f%z')

    # Convert the struct_time object into seconds since the epoch
    seconds_since_epoch = time.mktime(struct_time)

    # Calculate nanoseconds since the epoch
    nanoseconds_since_epoch = int(seconds_since_epoch * 1e9)

    return nanoseconds_since_epoch
