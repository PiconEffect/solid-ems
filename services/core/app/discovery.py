def publish_discovery(mqtt):
    sensors = {
        "pv_power": {"unit": "W"},
        "battery_soc": {"unit": "%"},
        "grid_power": {"unit": "W"},
        "load_power": {"unit": "W"},
        "battery_power": {"unit": "W"},
        "daily_energy": {"unit": "kWh"},
        "total_energy": {"unit": "kWh"},
        "inverter_temp": {"unit": "°C"},
        "advice": {},
        "tempo": {},
        "prediction": {},
        "pv_forecast_kw": {"unit": "kW"},
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

        if meta.get("unit"):
            config["unit_of_measurement"] = meta["unit"]

        mqtt.publish(f"homeassistant/sensor/solid/{name}/config", config)
