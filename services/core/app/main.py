import time
from solis_client import SolisClient
from mqtt import MqttClient
from discovery import publish_discovery
from ai_engine import AiEngine

client = SolisClient()
mqtt = MqttClient()
ai = AiEngine()

publish_discovery(mqtt)

while True:
    try:
        data = client.get_data()

        insight = ai.analyze(data)

        payload = {**data, **insight}

        mqtt.publish("solid/state", payload)

        print(payload)

    except Exception as e:
        print("ERROR:", e)

    time.sleep(3)
