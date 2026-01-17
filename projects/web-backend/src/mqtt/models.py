from django.db import models
import paho.mqtt.client as paho
from paho import mqtt


class MQTT(models.Model):
    def __init__(self, client_id="", userdata=None):
        self.client = paho.Client(
            client_id=client_id, userdata=userdata, protocol=paho.MQTTv5
        )

    def connect(self):
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        self.client.username_pw_set("Apple", "Dog")
        self.client.connect("159c683892ec4dbbaefa283364f7b6b3.s1.eu.hivemq.cloud", 8883)

    def publish(self, topic, payload_text, QOS_Level):
        self.client.publish(topic, payload=payload_text, qos=QOS_Level)


tempqtt = MQTT()
tempqtt.publish("topic/temperatures", "bonky", 1)
