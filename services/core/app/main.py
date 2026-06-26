import time
from solis_client import SolisClient
from mqtt import MqttClient
from discovery import publish_discovery

client = SolisClient()
mqtt = MqttClient()

publish_discovery(mqtt)

while True:
    try:
        data = client.get_data()
        mqtt.publish("solid/state", data)
        print("✅ Data sent", data)
    except Exception as e:
        print("❌ Error:", e)

    time.sleep(3)
