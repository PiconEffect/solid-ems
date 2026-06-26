import json
import os
import paho.mqtt.client as mqtt

class MqttClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.connect(os.getenv("MQTT_HOST"), int(os.getenv("MQTT_PORT")))
        self.client.loop_start()

    def publish(self, topic, payload):
        self.client.publish(topic, json.dumps(payload))
