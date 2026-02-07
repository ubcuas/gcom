import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
import json

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD")
MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS")
MQTT_TOPIC_ACK = os.getenv("MQTT_TOPIC_ACK")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        # client.subscribe(MQTT_TOPIC_CMD)
        # client.subscribe(MQTT_TOPIC_STATUS)
        client.subscribe(MQTT_TOPIC_ACK)
    else:
        print(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        message = msg.payload.decode("utf-8")
        print(f"Received message: {message} {topic}")
        return message

    except json.JSONDecodeError:
        print("Error decoding MQTT message")


def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT Broker")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.connect(MQTT_BROKER, MQTT_PORT)

message = """{"action":"TAKE_PHOTO"}"""


client.publish(MQTT_TOPIC_CMD, message)

client.loop_start()
