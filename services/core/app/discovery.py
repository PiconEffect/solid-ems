def publish_discovery(mqtt):
    sensors = {
        # -------------------------
        # Main-charging",        # Main sensors
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

        # -------------------------
        # AI / assistant sensors
        # -------------------------
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

        # -------------------------
        # Diagnostic raw Solis values
        # Useful to verify mapping
        # -------------------------
        "raw_power": {
            "name": "Raw Power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:alpha-p-circle",
        },
        "raw_pac": {
            "name": "Raw PAC",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:sine-wave",
        },
        "raw_pow1_kw": {
            "name": "Raw MPPT1",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel",
        },
        "raw_pow2_kw": {
            "name": "Raw MPPT2",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel-large",
        },
        "raw_pv_dc_kw": {
            "name": "Raw PV DC",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-power-variant",
        },
        "raw_family_load": {
            "name": "Raw Family Load",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:home-lightning-bolt",
        },
        "raw_total_load": {
            "name": "Raw Total Load",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:home-lightning-bolt-outline",
        },
        "raw_grid_psum": {
            "name": "Raw Grid PSUM",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:transmission-tower",
        },
        "raw_battery_power": {
            "name": "Raw Battery Power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:battery-charging",
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
            "force_update": True,
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
        # -------------------------
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
