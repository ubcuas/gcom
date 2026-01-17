from django.db import models
import paho.mqtt.client as paho
from paho import mqtt


class MQTT(models.Model):
    def on_connect(client, userdata, flags, rc, properties=None):
        print("CONNACK received with code %s." % rc)

    def on_publish(client, userdata, mid, properties=None):
        print("mid: " + str(mid))

    def on_subscribe(client, userdata, mid, granted_qos, properties=None):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
    client.on_connect = on_connect

    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    client.username_pw_set("Apple", "Doggy123")
    client.connect("159c683892ec4dbbaefa283364f7b6b3.s1.eu.hivemq.cloud", 8883)

    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_publish = on_publish

    client.subscribe("encyclopedia/#", qos=1)

    client.publish("encyclopedia/temperature", payload="hot", qos=1)

    client.loop_forever()
