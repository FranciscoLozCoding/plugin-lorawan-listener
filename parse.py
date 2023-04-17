import json
import logging

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