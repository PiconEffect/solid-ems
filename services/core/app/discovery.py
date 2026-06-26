def publish_discovery(mqtt):
    sensors = {
        "pv_power": "W",
        "battery_soc": "%",
        "grid_power": "W",
        "load_power": "W",
        "battery_power": "W",
        "daily_energy": "kWh",
        "total_energy": "kWh",
        "inverter_temp": "°C"
    }

    for name, unit in sensors.items():
        config = {
            "name": f"SOLID {name}",
            "state_topic": "solid/state",
            "value_template": f"{{{{ value_json.{name} }}}}",
            "unit_of_measurement": unit,
            "device": {
                "identifiers": ["solid_ems"],
                "name": "SOLID EMS",
                "manufacturer": "Custom"
            }
        }

        topic = f"homeassistant/sensor/solid/{name}/config"
        mqtt.publish(topic, config)
