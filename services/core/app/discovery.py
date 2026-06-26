def publish_discovery(mqtt):
    sensors = {
        "pv_power": {"unit": "W", "device_class": "power"},
        "battery_soc": {"unit": "%", "device_class": "battery"},
        "grid_power": {"unit": "W", "device_class": "power"},
        "load_power": {"unit": "W", "device_class": "power"},
        "battery_power": {"unit": "W", "device_class": "power"},
        "daily_energy": {"unit": "kWh", "device_class": "energy"},
        "total_energy": {"unit": "kWh", "device_class": "energy"},
        "inverter_temp": {"unit": "°C", "device_class": "temperature"},
        "advice": {},
        "tempo": {},
        "prediction": {},
    }

    for name, meta in sensors.items():
        config = {
            "name": f"SOLID {name}",
            "state_topic": "solid/state",
            "value_template": f"{{{{ value_json.{name} }}}}",
            "unique_id": f"solid_{name}",
            "device": {
                "identifiers": ["solid_ems"],
                "name": "SOLID EMS",
            },
        }

        if "unit" in meta:
            config["unit_of_measurement"] = meta.get("unit")

        if "device_class" in meta:
            config["device_class"] = meta.get("device_class")

        mqtt.publish(f"homeassistant/sensor/solid/{name}/config", config)

