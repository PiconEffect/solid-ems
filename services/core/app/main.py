import os
import time

from ai_engine import AiEngine
from discovery import publish_discovery
from mqtt import MqttClient
from solis_client import SolisClient


def main():
    print("SOLID EMS starting...", flush=True)

    poll_interval = int(os.getenv("POLL_INTERVAL", "30"))

    client = SolisClient()
    mqtt = MqttClient()
    ai = AiEngine()

    publish_discovery(mqtt)

    print(f"Polling interval: {poll_interval}s", flush=True)

    while True:
        try:
            data = client.get_data()

            if not data:
                print("No Solis data received, publishing AI/status only", flush=True)
                data = {}

            ai_data = ai.analyze(data)

            payload = {
                **data,
                **ai_data,
            }

            mqtt.publish("solid/state", payload, retain=True)

            print("Published state:", payload, flush=True)

        except Exception as error:
            print("MAIN ERROR:", error, flush=True)

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
