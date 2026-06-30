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


def tpl_autoconso():
    return (
        "{% set pv = value_json.pv_power | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% if pv > 0 %}"
        "{% set used = load if load < pv else pv %}"
        "{{ (used / pv * 100) | round(1) }}"
        "{% else %}0{% endif %}"
    )


def tpl_prevision_conso():
    return (
        "{% set habit = value_json.habit_load_next_6h_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% if habit > 0 %}"
        "{{ habit | round(2) }}"
        "{% else %}"
        "{{ load | round(2) }}"
        "{% endif %}"
    )


def tpl_ecart_prev_conso():
    return (
        "{% set habit = value_json.habit_load_next_6h_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% set conso = habit if habit > 0 else load %}"
        "{% set pvf = value_json.pv_forecast_kw | float(0) %}"
        "{{ (conso - pvf) | round(2) }}"
    )


NUMERIC_SENSORS = [
    # -------------------------------------------------------------------------
    # Entités principales modernes
    # -------------------------------------------------------------------------
    {"key": "pv_power", "name": "PV Power", "object_id": "solid_pv_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "battery_soc", "name": "Battery SOC", "object_id": "solid_battery_soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery"},
    {"key": "grid_power", "name": "Grid Power", "object_id": "solid_grid_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    {"key": "load_power", "name": "Load Power", "object_id": "solid_load_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    {"key": "battery_power", "name": "Battery Power", "object_id": "solid_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},

    # -------------------------------------------------------------------------
    # Entités exactes vues dans tes dashboards YAML
    # -------------------------------------------------------------------------
    {"key": "pv_power", "name": "Legacy PV Power", "object_id": "solid_ems_solid_pv_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "battery_soc", "name": "Legacy Battery SOC", "object_id": "solid_ems_solid_battery_soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery"},
    {"key": "battery_power", "name": "Legacy Battery Power", "object_id": "solid_ems_solid_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},
    {"key": "pv_forecast_kw", "name": "Legacy PV Forecast", "object_id": "solid_ems_solid_pv_forecast", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny"},

    {"key": "pv_power", "name": "Legacy PV Power", "object_id": "panneaux_solaires_solid_ems_solid_pv_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "battery_soc", "name": "Legacy Battery SOC", "object_id": "panneaux_solaires_solid_ems_solid_battery_soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery"},
    {"key": "battery_power", "name": "Legacy Battery Power", "object_id": "panneaux_solaires_solid_ems_solid_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},

    # -------------------------------------------------------------------------
    # Entités exactes actuellement visibles dans Home Assistant
    # -------------------------------------------------------------------------
    {"name": "Batt Pleine", "object_id": "panneaux_solaires_solid_ems_batt_pleine", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Battery Full Calculated", "object_id": "panneaux_solaires_solid_ems_battery_full_calculated", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Ecart Prevision Conso", "object_id": "panneaux_solaires_solid_ems_ecart_prevision_conso", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prev_conso()},
    {"name": "Forecast Load Gap", "object_id": "panneaux_solaires_solid_ems_forecast_load_gap", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prev_conso()},

    # -------------------------------------------------------------------------
    # Anciennes entités legacy visibles dans HA
    # -------------------------------------------------------------------------
    {"name": "Legacy Batt Pleine", "object_id": "panneaux_solaires_solid_ems_legacy_batt_pleine", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Legacy Batt Pleine 2", "object_id": "panneaux_solaires_solid_ems_legacy_batt_pleine_2", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Legacy Battery Full Calculated", "object_id": "panneaux_solaires_solid_ems_legacy_battery_full_calculated", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Legacy Battery Full Calculated 2", "object_id": "panneaux_solaires_solid_ems_legacy_battery_full_calculated_2", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Legacy Ecart Prevision Conso", "object_id": "panneaux_solaires_solid_ems_legacy_ecart_prevision_conso", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prev_conso()},
    {"name": "Legacy Ecart Prevision Conso 2", "object_id": "panneaux_solaires_solid_ems_legacy_ecart_prevision_conso_2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prev_conso()},

    # -------------------------------------------------------------------------
    # Calculs modernes utiles
    # -------------------------------------------------------------------------
    {"name": "Autoconso", "object_id": "solid_autoconso_pct", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:home-percent", "template": tpl_autoconso()},
    {"name": "Autoconsumption", "object_id": "solid_autoconsumption_pct", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:home-percent", "template": tpl_autoconso()},
    {"name": "Autoconso", "object_id": "panneaux_solaires_solid_ems_autoconso", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:home-percent", "template": tpl_autoconso()},
    {"name": "Autoconso pct", "object_id": "panneaux_solaires_solid_ems_autoconso_pct", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:home-percent", "template": tpl_autoconso()},

    {"name": "Batt Pleine", "object_id": "solid_batt_pleine_h", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Battery Full Calculated", "object_id": "solid_battery_full_calc_h", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"name": "Prevision Conso", "object_id": "solid_prevision_conso_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-clock", "template": tpl_prevision_conso()},
    {"name": "Ecart Prevision Conso", "object_id": "solid_ecart_prev_conso_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prev_conso()},
    {"name": "Forecast Load Gap", "object_id": "solid_forecast_load_gap_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prev_conso()},

    # -------------------------------------------------------------------------
    # PV / raw / diagnostics
    # -------------------------------------------------------------------------
    {"key": "pv1_power", "name": "PV1 Power", "object_id": "solid_pv1_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    {"key": "pv2_power", "name": "PV2 Power", "object_id": "solid_pv2_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    {"key": "pv_total_dc_power", "name": "PV Total DC Power", "object_id": "solid_pv_total_dc_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power-variant"},
    {"key": "pv_string_imbalance_pct", "name": "PV String Imbalance", "object_id": "solid_pv_string_imbalance_pct", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:solar-panel-large"},
    {"key": "pv_string_imbalance_pct", "name": "SOLID PV String Individual Deviation", "object_id": "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:solar-panel-large"},
    {"key": "raw_battery_power", "name": "Raw Battery Power", "object_id": "panneaux_solaires_solid_ems_solid_raw_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},

    # -------------------------------------------------------------------------
    # Sources directes IA / forecast
    # -------------------------------------------------------------------------
    {"key": "pv_forecast_kw", "name": "PV Forecast", "object_id": "solid_pv_forecast_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny"},
    {"key": "habit_load_next_6h_kw", "name": "Habit Load Next 6h", "object_id": "solid_habit_load_next_6h_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-clock"},
    {"key": "estimated_battery_full_h", "name": "Estimated Battery Full Source", "object_id": "solid_estimated_battery_full_h", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock"},
]


TEXT_SENSORS = [
    {"key": "advice", "name": "AI Advice", "object_id": "solid_advice", "icon": "mdi:lightbulb-on-outline"},
    {"key": "advice", "name": "Supervision IA", "object_id": "solid_supervision_ia", "icon": "mdi:brain"},
    {"key": "advice", "name": "Legacy AI Advice", "object_id": "panneaux_solaires_solid_ems_legacy_ai_advice", "icon": "mdi:brain"},
    {"key": "advice", "name": "Legacy AI Advice 2", "object_id": "panneaux_solaires_solid_ems_legacy_ai_advice_2", "icon": "mdi:brain"},

    {"key": "prediction", "name": "AI Prediction", "object_id": "solid_prediction", "icon": "mdi:crystal-ball"},
    {"key": "prediction", "name": "Legacy AI Prediction", "object_id": "panneaux_solaires_solid_ems_legacy_ai_prediction", "icon": "mdi:crystal-ball"},
    {"key": "prediction", "name": "Legacy AI Prediction 2", "object_id": "panneaux_solaires_solid_ems_legacy_ai_prediction_2", "icon": "mdi:crystal-ball"},

    {"key": "energy_mode", "name": "Energy Mode", "object_id": "solid_energy_mode", "icon": "mdi:home-lightning-bolt"},
    {"key": "battery_strategy", "name": "Battery Strategy", "object_id": "solid_battery_strategy", "icon": "mdi:battery-heart"},
    {"key": "battery_strategy", "name": "Battery Strategy", "object_id": "panneaux_solaires_solid_ems_solid_battery_strategy", "icon": "mdi:battery-heart"},

    {"key": "pv_string_status", "name": "PV String Status", "object_id": "solid_pv_string_status", "icon": "mdi:solar-panel"},
    {"key": "pv_string_status", "name": "PV String Status", "object_id": "panneaux_solaires_solid_ems_solid_pv_string_status", "icon": "mdi:solar-panel"},
    {"key": "pv_string_alert", "name": "PV String Alert", "object_id": "solid_pv_string_alert", "icon": "mdi:alert-circle-outline"},
    {"key": "pv_string_alert", "name": "Diagnostic PV", "object_id": "solid_diag_pv", "icon": "mdi:solar-panel-large"},

    {"key": "tempo_label", "name": "Tempo Label", "object_id": "solid_tempo_label", "icon": "mdi:calendar-today"},
    {"key": "tempo_tomorrow_label", "name": "Tempo Tomorrow Label", "object_id": "solid_tempo_tomorrow_label", "icon": "mdi:calendar-arrow-right"},
    {"key": "timestamp", "name": "Timestamp", "object_id": "solid_timestamp", "icon": "mdi:clock-outline"},
]


def _dedupe(items):
    result = {}
    for item in items:
        result[item["object_id"]] = item
    return list(result.values())


def _publish_config(mqtt, topic, config):
    mqtt.publish(topic, payload=json.dumps(config, ensure_ascii=False), qos=0, retain=True)
    print(f"MQTT Discovery published -> {topic}", flush=True)


def _numeric_config(sensor, state_topic):
    template = sensor.get("template") or tpl_num(sensor["key"])

    config = {
        "name": sensor["name"],
        "object_id": sensor["object_id"],
        "unique_id": sensor["object_id"],
        "state_topic": state_topic,
        "value_template": template,
        "device": DEVICE,
        "icon": sensor.get("icon"),
    }

    if sensor.get("unit") is not None:
        config["unit_of_measurement"] = sensor["unit"]

    if sensor.get("device_class") is not None:
        config["device_class"] = sensor["device_class"]

    if sensor.get("state_class") is not None:
        config["state_class"] = sensor["state_class"]

    return config


def _text_config(sensor, state_topic):
    return {
        "name": sensor["name"],
        "object_id": sensor["object_id"],
        "unique_id": sensor["object_id"],
        "state_topic": state_topic,
        "value_template": tpl_txt(sensor["key"]),
        "device": DEVICE,
        "icon": sensor.get("icon"),
    }


def publish_discovery(mqtt, state_topic=STATE_TOPIC_DEFAULT, *args, **kwargs):
    discovery_prefix = kwargs.get("discovery_prefix", DISCOVERY_PREFIX_DEFAULT)

    print(
        f"MQTT Discovery publish started state_topic={state_topic} prefix={discovery_prefix}",
        flush=True,
    )

    numeric_sensors = _dedupe(NUMERIC_SENSORS)
    text_sensors = _dedupe(TEXT_SENSORS)

    for sensor in numeric_sensors:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _numeric_config(sensor, state_topic))

    for sensor in text_sensors:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _text_config(sensor, state_topic))

    print(
        f"MQTT Discovery publish completed numeric={len(numeric_sensors)} text={len(text_sensors)}",
        flush=True,
    )
