import logging
import base64
import time
from waggle.plugin import Plugin
from parse import parse_message_payload
from parse import clean_message_dict

def on_message_publish(client, userdata, message):

    log_message(message) #log message

    try: #get metadata and data received in bytes
        metadata = parse_message_payload(message.payload.decode("utf-8"))
        bytes_b64 = metadata["data"].encode("utf-8")
    except:
        logging.error("Message did not contain data.")
        return

    #decode data
    bytes = base64.b64decode(bytes_b64) 
    val = bytes.decode("utf-8")

    #if number convert to int
    try:
        val = int(val)
    except:
        pass

    #remove dynamic metadata
    try:
        metadata = clean_message_dict(metadata)
    except:
        return

    with Plugin() as plugin: #publish lorawan data
        plugin.publish("lorawan.data", val, timestamp=time.time_ns(), meta=metadata)

    return

def on_message_dry(client, userdata, message):

    log_message(message) #log message

    return

def log_message(message):
        
    data = (
        "LORAWAN Message received: " + message.payload.decode("utf-8") + " with topic " + str(message.topic)
    )
    logging.info(data) #log message received

    return