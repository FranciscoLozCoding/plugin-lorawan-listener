import logging

def on_connect(client, userdata, flags, rc,subcribe_topic):
    logging.info("Connected: " + str(rc))
    logging.info(f"subscribing [{subcribe_topic}]...")
    client.subscribe(subcribe_topic)

def on_subscribe(client, obj, mid, granted_qos):
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    logging.debug(string)