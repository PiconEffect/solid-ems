def publish_discovery(mqtt):
    sensors = {
        "pv_power": {
            "name": "PV Power "object_id": "solid_ems_solid_pv_string_1_power",            "name": "PV Power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel",
        },
        "pv2_power": {
            "name": "PV String 2 Power",
            "object_id": "solid_ems_solid_pv_string_2_power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel-large",
        },
        "pv_total_dc_power": {
            "name": "PV DC Total Power",
            "object_id": "solid_ems_solid_pv_dc_total_power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-power-variant",
        },
        "advice": {
            "name": "AI Advice",
            "object_id": "solid_ems_solid_ai_advice",
            "icon": "mdi:brain",
        },
        "prediction": {
            "name": "Prediction",
            "object_id": "solid_ems_solid_prediction",
            "icon": "mdi:crystal-ball",
        },
        "energy_mode": {
            "name": "Energy Mode",
            "object_id": "solid_ems_solid_energy_mode",
            "icon": "mdi:home-lightning-bolt",
        },
        "battery_strategy": {
            "name": "Battery Strategy",
            "object_id": "solid_ems_solid_battery_strategy",
            "icon": "mdi:battery-clock",
        },
        "estimated_autonomy_h": {
            "name": "Estimated Autonomy",
            "object_id": "solid_ems_solid_estimated_autonomy",
            "unit": "h",
            "state_class": "measurement",
            "icon": "mdi:timer-sand",
        },
        "estimated_battery_full_h": {
            "name": "Estimated Battery Full",
            "object_id": "solid_ems_solid_estimated_battery_full",
            "unit": "h",
            "state_class": "measurement",
            "icon": "mdi:battery-clock",
        },
        "habit_load_now_kw": {
            "name": "Habit Load Now",
            "object_id": "solid_ems_solid_habit_load_now",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:chart-bell-curve",
        },
        "habit_load_next_6h_kw": {
            "name": "Habit Load Next 6h",
            "object_id": "solid_ems_solid_habit_load_next_6h",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:chart-timeline-variant",
        },
        "advice_priority": {
            "name": "AI Advice Priority",
            "object_id": "solid_ems_solid_ai_advice_priority",
            "state_class": "measurement",
            "icon": "mdi:alert-decagram",
        },
        "advice_confidence": {
            "name": "AI Advice Confidence",
            "object_id": "solid_ems_solid_ai_advice_confidence",
            "icon": "mdi:shield-check",
        },
        "pv_forecast_kw": {
            "name": "PV Forecast",
            "object_id": "solid_ems_solid_pv_forecast",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:weather-sunny",
        },
        "pv_string_status": {
            "name": "PV String Status",
            "object_id": "solid_ems_solid_pv_string_status",
            "icon": "mdi:solar-panel",
        },
        "pv_string_alert": {
            "name": "PV String Alert",
            "object_id": "solid_ems_solid_pv_string_alert",
            "icon": "mdi:alert-circle",
        },
        "pv_string_imbalance_pct": {
            "name": "PV String Individual Deviation",
            "object_id": "solid_ems_solid_pv_string_individual_deviation",
            "unit": "%",
            "state_class": "measurement",
            "icon": "mdi:scale-unbalanced",
        },
        "tempo": {
            "name": "Tempo",
            "object_id": "solid_ems_solid_tempo",
            "icon": "mdi:calendar-today",
        },
        "tempo_label": {
            "name": "Tempo Label",
            "object_id": "solid_ems_solid_tempo_label",
            "icon": "mdi:palette",
        },
        "tempo_tomorrow": {
            "name": "Tempo Tomorrow",
            "object_id": "solid_ems_solid_tempo_tomorrow",
            "icon": "mdi:calendar-arrow-right",
        },
        "tempo_tomorrow_label": {
            "name": "Tempo Tomorrow Label",
            "object_id": "solid_ems_solid_tempo_tomorrow_label",
            "icon": "mdi:palette-outline",
        },
        "raw_power": {
            "name": "Raw Power",
            "object_id": "solid_ems_solid_raw_power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:alpha-p-circle",
        },
        "raw_pac": {
            "name": "Raw PAC",
            "object_id": "solid_ems_solid_raw_pac",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:sine-wave",
        },
        "raw_pow1_kw": {
            "name": "Raw MPPT1",
            "object_id": "solid_ems_solid_raw_mppt1",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel",
        },
        "raw_pow2_kw": {
            "name": "Raw MPPT2",
            "object_id": "solid_ems_solid_raw_mppt2",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel-large",
        },
        "raw_pv_dc_kw": {
            "name": "Raw PV DC",
            "object_id": "solid_ems_solid_raw_pv_dc",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-power-variant",
        },
        "raw_family_load": {
            "name": "Raw Family Load",
            "object_id": "solid_ems_solid_raw_family_load",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:home-lightning-bolt",
        },
        "raw_total_load": {
            "name": "Raw Total Load",
            "object_id": "solid_ems_solid_raw_total_load",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:home-lightning-bolt-outline",
        },
        "raw_grid_psum": {
            "name": "Raw Grid PSUM",
            "object_id": "solid_ems_solid_raw_grid_psum",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:transmission-tower",
        },
        "raw_battery_power": {
            "name": "Raw Battery Power",
            "object_id": "solid_ems_solid_raw_battery_power",
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
            "object_id": meta.get("object_id"),
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
            "object_id": "solid_ems_solid_pv_power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-power",
        },
        "battery_soc": {
            "name": "Battery SOC",
            "object_id": "solid_ems_solid_battery_soc",
            "unit": "%",
            "device_class": "battery",
            "state_class": "measurement",
            "icon": "mdi:battery",
        },
        "grid_power": {
            "name": "Grid Power",
            "object_id": "solid_ems_solid_grid_power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:transmission-tower",
        },
        "load_power": {
            "name": "Home Load",
            "object_id": "solid_ems_solid_home_load",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:home-lightning-bolt",
        },
        "battery_power": {
            "name": "Battery Power",
            "object_id": "solid_ems_solid_battery_power",
            "unit": "kW",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:battery-charging",
        },
        "daily_energy": {
            "name": "Daily Energy",
            "object_id": "solid_ems_solid_daily_energy",
            "unit": "kWh",
            "device_class": "energy",
            "state_class": "total_increasing",
            "icon": "mdi:counter",
        },
        "total_energy": {
            "name": "Total Energy",
            "object_id": "solid_ems_solid_total_energy",
            "unit": "MWh",
            "device_class": "energy",
            "state_class": "total_increasing",
            "icon": "mdi:counter",
        },
        "inverter_temp": {
            "name": "Inverter Temperature",
            "object_id": "solid_ems_solid_inverter_temperature",
            "unit": "\u00b0C",
            "device_class": "temperature",
            "state_class": "measurement",
            "icon": "mdi:thermometer",
        },
        "pv1_power": {
            "name": "PV String 1 Power",
