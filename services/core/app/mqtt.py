import json
import os
import paho.mqtt.client as mqtt


class MqttClient:
    def __init__(self):
        self.host = os.getenv("MQTT_HOST", "mqtt")
        self.port = int(os.getenv("MQTT_PORT", "1883"))

        self.client = mqtt.Client()
        self.client.connect(self.host, self.port, 60)
        self.client.loop_start()

        print(f"MQTT connected to {self.host}:{self.port}", flush=True)

    def publish(self, topic, payload, retain=False):
        self.client.publish(
            topic,
            json.dumps(payload),
            retain=retain,
        )
