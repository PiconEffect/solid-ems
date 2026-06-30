import json


STATE_TOPIC_DEFAULT = "solid/state"
DISCOVERY_PREFIX_DEFAULT = "homeassistant"


DEVICE = {
    "identifiers": ["solid_ems"],
    "name": "SOLID EMS",
    "manufacturer": "SOLID EMS",
    "model": "Solis EMS Monitor",
}


def tpl_num(key):
    return "{{ value_json." + key + " | default(0) | float(0) }}"


def tpl_txt(key):
    return "{{ value_json." + key + " | default('') }}"


def tpl_batt_full():
    return (
        "{% set soc = value_json.battery_soc | float(0) %}"
        "{% set p = value_json.battery_power | float(0) %}"
        "{% set cap = 30 %}"
        "{% if p > 0 and soc < 100 %}"
        "{{ (((100 - soc) / 100 * cap) / p) | round(2) }}"
        "{% else %}0{% endif %}"
    )


def tpl_autonomy():
    return (
        "{% set soc = value_json.battery_soc | float(0) %}"
        "{% set p = value_json.battery_power | float(0) %}"
        "{% set cap = 30 %}"
        "{% if p < 0 and soc > 0 %}"
        "{{ ((soc / 100 * cap) / (p | abs)) | round(2) }}"
        "{% else %}0{% endif %}"
    )


def tpl_pv_forecast_fallback():
    return (
        "{% set pvf = value_json.pv_forecast_kw | float(0) %}"
        "{% set pv = value_json.pv_power | float(0) %}"
        "{% if pvf > 0 %}"
        "{{ pvf | round(2) }}"
        "{% else %}"
        "{{ pv | round(2) }}"
        "{% endif %}"
    )


def tpl_habit_load_now_fallback():
    return (
        "{% set habit = value_json.habit_load_now_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% if habit > 0 %}"
        "{{ habit | round(2) }}"
        "{% else %}"
        "{{ load | round(2) }}"
        "{% endif %}"
    )


def tpl_habit_load_next_6h_fallback():
    return (
        "{% set habit = value_json.habit_load_next_6h_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% if habit > 0 %}"
        "{{ habit | round(2) }}"
        "{% else %}"
        "{{ load | round(2) }}"
        "{% endif %}"
    )


def tpl_pv_string_imbalance():
    return (
        "{% set src = value_json.pv_string_imbalance_pct | float(0) %}"
        "{% set pv1 = value_json.pv1_power | float(0) %}"
        "{% set pv2 = value_json.pv2_power | float(0) %}"
        "{% set den = pv1 + pv2 %}"
        "{% if src > 0 %}"
        "{{ src | round(1) }}"
        "{% elif den > 0 %}"
        "{{ (((pv1 - pv2) | abs) / den * 100) | round(1) }}"
        "{% else %}0{% endif %}"
    )


SENSORS = {
    # -------------------------------------------------------------------------
    # Dashboard principal SOLID EMS
    # -------------------------------------------------------------------------
    "solid_ems_solid_pv_power": {
        "name": "PV Power",
        "key": "pv_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
    },
    "solid_ems_solid_battery_soc": {
        "name": "Battery SOC",
        "key": "battery_soc",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery",
    },
    "solid_ems_solid_grid_power": {
        "name": "Grid Power",
        "key": "grid_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
    },
    "solid_ems_solid_home_load": {
        "name": "Home Load",
        "key": "load_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
    },
    "solid_ems_solid_battery_power": {
        "name": "Battery Power",
        "key": "battery_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-charging",
    },
    "solid_ems_solid_daily_energy": {
        "name": "Daily Energy",
        "key": "daily_energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:counter",
    },
    "solid_ems_solid_total_energy": {
        "name": "Total Energy",
        "key": "total_energy",
        "unit": "MWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:counter",
    },
    "solid_ems_solid_tempo": {
        "name": "Tempo",
        "key": "tempo",
        "icon": "mdi:calendar-today",
    },

    # -------------------------------------------------------------------------
    # IA / supervision dashboard
    # -------------------------------------------------------------------------
    "solid_ems_solid_ai_advice": {
        "name": "AI Advice",
        "key": "advice",
        "icon": "mdi:brain",
        "text": True,
    },
    "solid_ems_solid_prediction": {
        "name": "Prediction",
        "key": "prediction",
        "icon": "mdi:crystal-ball",
        "text": True,
    },
    "panneaux_solaires_solid_ems_solid_energy_mode": {
        "name": "Energy Mode",
        "key": "energy_mode",
        "icon": "mdi:home-lightning-bolt",
        "text": True,
    },
    "panneaux_solaires_solid_ems_solid_battery_strategy": {
        "name": "Battery Strategy",
        "key": "battery_strategy",
        "icon": "mdi:battery-clock",
        "text": True,
    },
    "panneaux_solaires_solid_ems_solid_ai_advice_priority": {
        "name": "AI Advice Priority",
        "key": "advice_priority",
        "state_class": "measurement",
        "icon": "mdi:alert-decagram",
    },
    "panneaux_solaires_solid_ems_solid_ai_advice_confidence": {
        "name": "AI Advice Confidence",
        "key": "advice_confidence",
        "icon": "mdi:shield-check",
        "text": True,
    },

    # -------------------------------------------------------------------------
    # IA numériques avec fallback
    # -------------------------------------------------------------------------
    "panneaux_solaires_solid_ems_solid_estimated_autonomy": {
        "name": "Estimated Autonomy",
        "unit": "h",
        "state_class": "measurement",
        "icon": "mdi:timer-sand",
        "template": tpl_autonomy(),
    },
    "panneaux_solaires_solid_ems_solid_estimated_battery_full": {
        "name": "Estimated Battery Full",
        "unit": "h",
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": tpl_batt_full(),
    },
    "panneaux_solaires_solid_ems_solid_habit_load_now": {
        "name": "Habit Load Now",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:chart-bell-curve",
        "template": tpl_habit_load_now_fallback(),
    },
    "panneaux_solaires_solid_ems_solid_habit_load_next_6h": {
        "name": "Habit Load Next 6h",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:chart-timeline-variant",
        "template": tpl_habit_load_next_6h_fallback(),
    },
    "panneaux_solaires_solid_ems_solid_pv_forecast": {
        "name": "PV Forecast",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },
    "solid_ems_solid_pv_forecast": {
        "name": "PV Forecast",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },

    # -------------------------------------------------------------------------
    # PV strings / diagnostic
    # -------------------------------------------------------------------------
    "panneaux_solaires_solid_ems_solid_pv_string_1_power": {
        "name": "PV String 1 Power",
        "key": "pv1_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-panel",
    },
    "panneaux_solaires_solid_ems_solid_pv_string_2_power": {
        "name": "PV String 2 Power",
        "key": "pv2_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
    },
    "panneaux_solaires_solid_ems_solid_pv_dc_total_power": {
        "name": "PV DC Total Power",
        "key": "pv_total_dc_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power-variant",
    },
    "panneaux_solaires_solid_ems_solid_pv_string_status": {
        "name": "PV String Status",
        "key": "pv_string_status",
        "icon": "mdi:solar-panel",
        "text": True,
    },
    "panneaux_solaires_solid_ems_solid_pv_string_alert": {
        "name": "PV String Alert",
        "key": "pv_string_alert",
        "icon": "mdi:alert-circle",
        "text": True,
    },
    "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation": {
        "name": "PV String Individual Deviation",
        "unit": "%",
        "state_class": "measurement",
        "icon": "mdi:scale-unbalanced",
        "template": tpl_pv_string_imbalance(),
    },

    # -------------------------------------------------------------------------
    # Raw values dashboard
    # -------------------------------------------------------------------------
    "panneaux_solaires_solid_ems_solid_raw_battery_power": {
        "name": "Raw Battery Power",
        "key": "raw_battery_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-charging",
    },
    "panneaux_solaires_solid_ems_solid_raw_family_load": {
        "name": "Raw Family Load",
        "key": "raw_family_load",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
    },
    "panneaux_solaires_solid_ems_solid_raw_total_load": {
        "name": "Raw Total Load",
        "key": "raw_total_load",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt-outline",
    },
    "panneaux_solaires_solid_ems_solid_raw_pac": {
        "name": "Raw PAC",
        "key": "raw_pac",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:sine-wave",
    },
    "panneaux_solaires_solid_ems_solid_raw_pv_dc": {
        "name": "Raw PV DC",
        "key": "raw_pv_dc_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power-variant",
    },

    # -------------------------------------------------------------------------
    # Tempo labels dashboard
    # -------------------------------------------------------------------------
    "panneaux_solaires_solid_ems_solid_tempo_label": {
        "name": "Tempo Label",
        "key": "tempo_label",
        "icon": "mdi:palette",
        "text": True,
    },
    "panneaux_solaires_solid_ems_solid_tempo_tomorrow": {
        "name": "Tempo Tomorrow",
        "key": "tempo_tomorrow",
        "icon": "mdi:calendar-arrow-right",
    },
    "panneaux_solaires_solid_ems_solid_tempo_tomorrow_label": {
        "name": "Tempo Tomorrow Label",
        "key": "tempo_tomorrow_label",
        "icon": "mdi:palette-outline",
        "text": True,
    },
}


def _value_template(object_id, meta):
    if meta.get("template"):
        return meta["template"]

    key = meta.get("key")

    if meta.get("text"):
        return tpl_txt(key)

    return tpl_num(key)


def _publish_config(mqtt, topic, payload):
    mqtt.publish(
        topic,
        json.dumps(payload, ensure_ascii=False),
        retain=True,
    )
    print(f"MQTT Discovery published -> {topic}", flush=True)


def publish_discovery(mqtt, state_topic=STATE_TOPIC_DEFAULT, *args, **kwargs):
    """
    MQTT Discovery Home Assistant.

    Compatible avec :
      publish_discovery(mqtt)
      publish_discovery(mqtt, state_topic)
    """

    print("MQTT Discovery publish started", flush=True)

    for object_id, meta in SENSORS.items():
        config = {
            "name": meta["name"],
            "object_id": object_id,
            "unique_id": object_id,
            "state_topic": state_topic,
            "value_template": _value_template(object_id, meta),
            "device": DEVICE,
            "icon": meta.get("icon"),
        }

        if meta.get("unit") is not None:
            config["unit_of_measurement"] = meta["unit"]

        if meta.get("device_class") is not None:
            config["device_class"] = meta["device_class"]

        if meta.get("state_class") is not None:
            config["state_class"] = meta["state_class"]

        topic = f"{DISCOVERY_PREFIX_DEFAULT}/sensor/{object_id}/config"
        _publish_config(mqtt, topic, config)

    print(f"MQTT Discovery completed sensors={len(SENSORS)}", flush=True)
