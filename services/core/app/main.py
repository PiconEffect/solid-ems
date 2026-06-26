import time
from solis_client import SolisClient
from mqtt import MqttClient
from discovery import publish_discovery

client = SolisClient()
mqtt = MqttClient()

publish_discovery(mqtt)

while True:
    data = client.get_data()
    mqtt.publish("solid/state", data)
    time.sleep(3)
