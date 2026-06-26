def publish_discovery(mqtt):
    sensors = {
        "pv_power": {
            "unit": "W",
            "device_class": "power"
        },
        "battery_soc": {
            "unit": "%",
            "device_class": "battery"
        },
        "grid_power": {
            "unit": "W",
            "device_class": "power"
        },
        "load_power": {
            "unit": "W",
            "device_class": "power"
        },
        "battery_power": {
            "unit": "W",
            "device_class": "power"
        },
        "daily_energy": {
            "unit": "kWh",
            "device_class": "energy"
        },
        "total_energy": {
            "unit": "kWh",
            "device_class": "energy"
        },
        "inverter_temp": {
            "unit": "°C",
            "device_class": "temperature"
        },
        # 🧠 IA
        "advice": {
            "unit": None,
            "device_class": None
        }
    }

    for name, meta in sensors.items():
        config = {
            "name": f"SOLID {name}",
            "state_topic": "solid/state",
            "value_template": f"{{{{ value_json.{name} }}}}",
            "device": {
                "identifiers": ["solid_ems"],
                "name": "SOLID EMS",
                "manufacturer": "Custom"
            }
        }

        # ✅ Ajouter unité si dispo
        if meta["unit"]:
            config["unit_of_measurement"] = meta["unit"]

        # ✅ Ajouter device class si dispo
        if meta["device_class"]:
            config["device_class"] = meta["device_class"]

        # ✅ Topic Home Assistant MQTT Discovery
        topic = f"homeassistant/sensor/solid/{name}/config"

        mqtt.publish(topic, config)
