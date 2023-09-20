import logging
import time
from waggle.plugin import Plugin
from parse import *

def on_message_publish(client, userdata, message,to_publish):
    print("measurements: %r" % to_publish)
    log_message(message) #log message

    try: #get metadata and measurements received
        metadata = parse_message_payload(message.payload.decode("utf-8"))
        measurements = metadata["object"]["measurements"]
    except:
        logging.error("Message did not contain measurements.")
        return

    #get chirpstack time and convert to time in nanoseconds
    timestamp = convert_time(metadata["time"])

    #remove dynamic metadata
    try:
        metadata = clean_message_dict(metadata)
    except:
        return
    
    for measurement in measurements:

        #clean measurement names
        measurement = clean_message_measurement(measurement)

        if to_publish: #true if not empty
            if measurement["name"] in to_publish: #if not empty only publish measurements in list
                publish(measurement,timestamp,metadata)
        else: #else to_publish is empty so publish all measurements
            publish(measurement,timestamp,metadata)


    return

def publish(measurement,timestamp,metadata):
    with Plugin() as plugin: #publish lorawan data
        try:
            plugin.publish(measurement["name"], measurement["value"], timestamp=timestamp, meta=metadata)

            # If the function succeeds, log a success message
            logging.info('%s published', measurement["name"])
        except Exception as e:
            # If an exception is raised, log an error message
            logging.error('measurement did not publish encountered an error: %s', str(e))


def on_message_dry(client, userdata, message):

    log_message(message)

    log_measurements(message)

    return

def log_message(message):
        
    data = (
        "LORAWAN Message received: " + message.payload.decode("utf-8") + " with topic " + str(message.topic)
    )
    logging.info(data) #log message received

    return

def log_measurements(message):

    try: #get metadata and measurements received
        metadata = parse_message_payload(message.payload.decode("utf-8"))
        measurements = metadata["object"]["measurements"]
    except:
        logging.error("Message did not contain measurements.")
        return
    
    for measurement in measurements:

        logging.info(str(measurement["name"]) + ": " + str(measurement["value"]))

    return