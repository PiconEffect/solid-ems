from ai_engine import AiEngine

ai = AiEngine()

while True:
    try:
        data = client.get_data()

        # 🧠 analyse IA
        insight = ai.analyze(data)

        # fusion data + IA
        payload = {**data, **insight}

        mqtt.publish("solid/state", payload)

        print("✅ Data:", payload)

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(3)
