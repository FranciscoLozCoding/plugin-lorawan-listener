"""
ChirpStack MQTT payload parsing and metadata helpers.

Parses JSON payloads, extracts device/metadata, normalizes measurement names (clean_string),
and converts timestamps. Used by the ChirpStack client and the shared publish pipeline.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from dateutil import parser

def parse_message_payload(payload_data: str) -> Dict[str, Any]:
    """Parse ChirpStack MQTT message payload JSON into a dict."""
    tmp_dict = json.loads(payload_data)
    return tmp_dict

def Get_Measurement_metadata(message_dict: Dict[str, Any]) -> Dict[str, Any]:
    tmp_dict = {}

    #Get static metadata
    tmp_dict['devAddr'] = message_dict.get('devAddr', None)
    tmp_dict['lns'] = 'local_chirpstack'

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

    #get tags
    tags_dict = deviceInfo_dict.get('tags', None)
    try:
        for key, value in tags_dict.items():
            key = clean_string(key)
            tmp_dict[key + "_tag"] = value
    except:
        pass

    #NOTE: NEVER get device variables, they hold sensitive data that should not be exposed.

    return tmp_dict

def clean_message_measurement(measurement: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize measurement name with clean_string (lowercase, alphanumeric + underscore)."""
    #clean name
    measurement["name"] = clean_string(measurement["name"])
    return measurement

def clean_string(txt: str) -> str:
    """Lowercase and replace non-alphanumeric/underscore with underscore (for measurement names)."""
    #convert capital letters to lowercase
    txt = txt.lower()

    #pattern excepted 
    pattern = r'[^a-z0-9_]'

    #replace not excepted values with '_' in txt
    txt = re.sub(pattern, '_', txt)

    return txt

def Get_Signal_Performance_values(message_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Get Lorawan Performance values from message_dict."""
    tmp_dict = {}

    #Get Lorawan Performance values
    tmp_dict['rxInfo'] = []
    if 'rxInfo' in message_dict:
        for val in message_dict['rxInfo']:
            temp = {
                "gatewayId": val.get('gatewayId', None),
                "rssi": val.get('rssi', None),
                "snr": val.get('snr', None)
            }
            tmp_dict['rxInfo'].append(temp)
    else:
        logging.error("rxInfo was not found")

    txInfo_dict = message_dict.get('txInfo', None)
    if (
        txInfo_dict
        and 'modulation' in txInfo_dict
        and 'lora' in txInfo_dict['modulation']
        and 'spreadingFactor' in txInfo_dict['modulation']['lora']
    ):
        tmp_dict['spreadingfactor'] = txInfo_dict['modulation']['lora']['spreadingFactor']
    else:
        tmp_dict['spreadingfactor'] = None
        logging.error("spreadingFactor was not found")

    tmp_dict['fCnt'] = message_dict.get('fCnt', None)

    return tmp_dict


def Get_Signal_Performance_metadata(message_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Get Lorawan Performance metadata from message_dict."""
    tmp_dict = {}

    #get values from nested dictionary
    deviceInfo_dict = message_dict.get('deviceInfo', None)
    try:
        tmp_dict['deviceName'] = deviceInfo_dict['deviceName']
        tmp_dict['devEui'] = deviceInfo_dict['devEui']
        tmp_dict['lns'] = 'local_chirpstack'
    except:
        logging.error("deviceInfo was not found")

    #get tags
    tags_dict = deviceInfo_dict.get('tags', None)
    try:
        for key, value in tags_dict.items():
            key = clean_string(key)
            tmp_dict[key + "_tag"] = value
    except:
        pass

    #NOTE: NEVER get device variables, they hold sensitive data that should not be exposed.

    return tmp_dict


def convert_time(iso_time: Any) -> Optional[int]:
    """Parse ISO timestamp string to nanoseconds since epoch. Returns None on parse failure."""
    try:
        datetime_obj = parser.isoparse(iso_time)
    except ValueError as e:
        logging.error(f"Error: {e}")
    else:
        # Convert the datetime object to nanoseconds since the epoch
        total_seconds = datetime_obj.timestamp()
        nanoseconds = int(total_seconds * 1e9)

    return nanoseconds
