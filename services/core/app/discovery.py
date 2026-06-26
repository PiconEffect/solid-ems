def publish_discovery(mqtt):
    sensors = {
        "pv_power": {
            "name": "PV Power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-power",
        },
        "battery_soc": {
            "name": "Battery SOC",
            "unit": "%",
            "device_class": "battery",
            "state_class": "measurement",
            "icon": "mdi:battery",
        },
        "grid_power": {
            "name": "Grid Power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:transmission-tower",
        },
        "load_power": {
            "name": "Home Load",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:home-lightning-bolt",
        },
        "battery_power": {
            "name": "Battery Power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:battery-charging",
        },
        "daily_energy": {
            "name": "Daily Energy",
            "unit": "kWh",
            "device_class": "energy",
            "state_class": "total_increasing",
            "icon": "mdi:counter",
        },
        "total_energy": {
            "name": "Total Energy",
            "unit": "MWh",
            "device_class": "energy",
            "state_class": "total_increasing",
            "icon": "mdi:counter",
        },
        "inverter_temp": {
            "name": "Inverter Temperature",
            "unit": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
            "icon": "mdi:thermometer",
        },
        "advice": {
            "name": "AI Advice",
            "icon": "mdi:brain",
        },
        "tempo": {
            "name": "Tempo",
            "icon": "mdi:calendar-clock",
        },
        "prediction": {
            "name": "Prediction",
            "icon": "mdi:crystal-ball",
        },
        "pv_forecast_kw": {
            "name": "PV Forecast",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:weather-sunny",
        },
    }

    device = {
        "identifiers": ["solid_ems"],
        "name": "SOLID EMS",
        "manufacturer": "SOLID EMS",
        "model": "Solis Energy Manager",
    }

    for key, meta in sensors.items():
        config = {
            "name": f"SOLID {meta['name']}",
            "unique_id": f"solid_{key}",
            "state_topic": "solid/state",
            "value_template": f"{{{{ value_json.{key} }}}}",
            "device": device,
            "icon": meta.get("icon"),
        }

        if meta.get("unit"):
            config["unit_of_measurement"] = meta["unit"]

        if meta.get("device_class"):
            config["device_class"] = meta["device_class"]

        if meta.get("state_class"):
            config["state_class"] = meta["state_class"]

        topic = f"homeassistant/sensor/solid/{key}/config"

        mqtt.publish(topic, config, retain=True)

    print("MQTT Discovery published", flush=True)
