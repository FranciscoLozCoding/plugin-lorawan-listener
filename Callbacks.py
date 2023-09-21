import logging

def on_connect(client, userdata, flags, rc):
    logging.info("rc: " + str(rc))

def on_subscribe(client, obj, mid, granted_qos):
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    logging.debug(string)