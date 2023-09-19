import logging
import time
from waggle.plugin import Plugin
from parse import parse_message_payload
from parse import clean_message_dict
from parse import clean_message_measurement

def on_message_publish(client, userdata, message):

    log_message(message) #log message

    try: #get metadata and measurements received
        metadata = parse_message_payload(message.payload.decode("utf-8"))
        measurements = metadata["object"]["measurements"]
    except:
        logging.error("Message did not contain measurements.")
        return

    #remove dynamic metadata
    try:
        metadata = clean_message_dict(metadata)
    except:
        return
    
    for measurement in measurements:

        #clean measurement names
        measurement = clean_message_measurement(measurement)

        with Plugin() as plugin: #publish lorawan data
            plugin.publish(measurement["name"], measurement["value"], timestamp=time.time_ns(), meta=metadata)

    return

def on_message_dry(client, userdata, message):

    log_message(message) #log message

    return

def log_message(message):
        
    data = (
        "LORAWAN Message received: " + message.payload.decode("utf-8") + " with topic " + str(message.topic)
    )
    logging.info(data) #log message received

    try: #get metadata and measurements received
        metadata = parse_message_payload(message.payload.decode("utf-8"))
        measurements = metadata["object"]["measurements"]
    except:
        logging.error("Message did not contain measurements.")
        return
    
    for measurement in measurements:

        #clean measurement names
        measurement = clean_message_measurement(measurement)

        logging.info(str(measurement["name"]) + ": " + str(measurement["value"]))

    return