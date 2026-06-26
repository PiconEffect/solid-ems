def publish_discovery(mqtt):
    sensors = ["pv_power", "battery_soc", "grid_power", "load_power"]

    for s in sensors:
        config = {
            "name": f"SOLID {s}",
            "state_topic": "solid/state",
            "value_template": f"{{{{ value_json.{s} }}}}"
        }

        topic = f"homeassistant/sensor/solid/{s}/config"
        mqtt.publish(topic, config)
