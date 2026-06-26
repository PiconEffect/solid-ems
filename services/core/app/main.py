import time
from solis_client import SolisClient
from mqtt import MqttClient
from discovery import publish_discovery
from ai_engine import AiEngine
import os

client = SolisClient()
mqtt = MqttClient()
ai = AiEngine()

publish_discovery(mqtt)

interval = int(os.getenv("POLL_INTERVAL", 3))

while True:
    try:
        data = client.get_data()

        ai_data = ai.analyze(data)

        payload = {
            **data,
            **ai_data
        }

        mqtt.publish("solid/state", payload)

        print("✅ DATA:", payload)

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(interval)
