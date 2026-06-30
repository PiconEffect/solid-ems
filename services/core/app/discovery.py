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
        "{% if pvf > 0 %}{{ pvf | round(2) }}{% else %}{{ pv | round(2) }}{% endif %}"
    )


def tpl_habit_load_now_fallback():
    return (
        "{% set habit = value_json.habit_load_now_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% if habit > 0 %}{{ habit | round(2) }}{% else %}{{ load | round(2) }}{% endif %}"
    )


def tpl_habit_load_next_6h_fallback():
    return (
        "{% set habit = value_json.habit_load_next_6h_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% if habit > 0 %}{{ habit | round(2) }}{% else %}{{ load | round(2) }}{% endif %}"
    )


def tpl_ecart_prevision_conso():
    return (
        "{% set habit = value_json.habit_load_next_6h_kw | float(0) %}"
        "{% set load = value_json.load_power | float(0) %}"
        "{% set conso = habit if habit > 0 else load %}"
        "{% set pvf = value_json.pv_forecast_kw | float(0) %}"
        "{% set pv = value_json.pv_power | float(0) %}"
        "{% set forecast = pvf if pvf > 0 else pv %}"
        "{{ (conso - forecast) | round(2) }}"
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


def tpl_pv_string_imbalance():
    return (
        "{% set src = value_json.pv_string_imbalance_pct | float(0) %}"
        "{% set pv1 = value_json.pv1_power | float(0) %}"
        "{% set pv2 = value_json.pv2_power | float(0) %}"
        "{% set den = pv1 + pv2 %}"
        "{% if src > 0 %}{{ src | round(1) }}"
        "{% elif den > 0 %}{{ (((pv1 - pv2) | abs) / den * 100) | round(1) }}"
        "{% else %}0{% endif %}"
    )


SENSORS = {
    # Flux principal / Solis de base
    "pv_power": {"name": "PV Power", "object_id": "solid_ems_solid_pv_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    "battery_soc": {"name": "Battery SOC", "object_id": "solid_ems_solid_battery_soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery"},
    "grid_power": {"name": "Grid Power", "object_id": "solid_ems_solid_grid_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    "load_power": {"name": "Home Load", "object_id": "solid_ems_solid_home_load", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    "battery_power": {"name": "Battery Power", "object_id": "solid_ems_solid_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},
    "daily_energy": {"name": "Daily Energy", "object_id": "solid_ems_solid_daily_energy", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:counter"},
    "total_energy": {"name": "Total Energy", "object_id": "solid_ems_solid_total_energy", "unit": "MWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:counter"},
    "inverter_temp": {"name": "Inverter Temperature", "object_id": "solid_ems_solid_inverter_temperature", "unit": "°C", "device_class": "temperature", "state_class": "measurement", "icon": "mdi:thermometer"},

    # PV / MPPT / raw
    "pv1_power": {"name": "PV String 1 Power", "object_id": "solid_ems_solid_pv_string_1_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    "pv2_power": {"name": "PV String 2 Power", "object_id": "solid_ems_solid_pv_string_2_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel-large"},
    "pv_total_dc_power": {"name": "PV DC Total Power", "object_id": "solid_ems_solid_pv_dc_total_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power-variant"},
    "raw_power": {"name": "Raw Power", "object_id": "solid_ems_solid_raw_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:alpha-p-circle"},
    "raw_pac": {"name": "Raw PAC", "object_id": "solid_ems_solid_raw_pac", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:sine-wave"},
    "raw_pow1_kw": {"name": "Raw MPPT1", "object_id": "solid_ems_solid_raw_mppt1", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    "raw_pow2_kw": {"name": "Raw MPPT2", "object_id": "solid_ems_solid_raw_mppt2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel-large"},
    "raw_pv_dc_kw": {"name": "Raw PV DC", "object_id": "solid_ems_solid_raw_pv_dc", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power-variant"},
    "raw_family_load": {"name": "Raw Family Load", "object_id": "solid_ems_solid_raw_family_load", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    "raw_total_load": {"name": "Raw Total Load", "object_id": "solid_ems_solid_raw_total_load", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt-outline"},
    "raw_grid_psum": {"name": "Raw Grid PSUM", "object_id": "solid_ems_solid_raw_grid_psum", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    "raw_battery_power": {"name": "Raw Battery Power", "object_id": "solid_ems_solid_raw_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},

    # IA / stratégie / forecast - noms originaux
    "advice": {"name": "AI Advice", "object_id": "solid_ems_solid_ai_advice", "icon": "mdi:brain"},
    "prediction": {"name": "Prediction", "object_id": "solid_ems_solid_prediction", "icon": "mdi:crystal-ball"},
    "energy_mode": {"name": "Energy Mode", "object_id": "solid_ems_solid_energy_mode", "icon": "mdi:home-lightning-bolt"},
    "battery_strategy": {"name": "Battery Strategy", "object_id": "solid_ems_solid_battery_strategy", "icon": "mdi:battery-clock"},
    "advice_priority": {"name": "AI Advice Priority", "object_id": "solid_ems_solid_ai_advice_priority", "state_class": "measurement", "icon": "mdi:alert-decagram"},
    "advice_confidence": {"name": "AI Advice Confidence", "object_id": "solid_ems_solid_ai_advice_confidence", "icon": "mdi:shield-check"},

    # Ces clés source valent parfois 0 dans solid/state. On publie les object_id originaux avec fallback plus bas en ALIASES.
    "estimated_autonomy_h": {"name": "Estimated Autonomy", "object_id": "solid_ems_solid_estimated_autonomy", "unit": "h", "state_class": "measurement", "icon": "mdi:timer-sand"},
    "estimated_battery_full_h": {"name": "Estimated Battery Full", "object_id": "solid_ems_solid_estimated_battery_full", "unit": "h", "state_class": "measurement", "icon": "mdi:battery-clock"},
    "habit_load_now_kw": {"name": "Habit Load Now", "object_id": "solid_ems_solid_habit_load_now", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-bell-curve"},
    "habit_load_next_6h_kw": {"name": "Habit Load Next 6h", "object_id": "solid_ems_solid_habit_load_next_6h", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-timeline-variant"},
    "pv_forecast_kw": {"name": "PV Forecast", "object_id": "solid_ems_solid_pv_forecast", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny"},

    # Diagnostic PV
    "pv_string_status": {"name": "PV String Status", "object_id": "solid_ems_solid_pv_string_status", "icon": "mdi:solar-panel"},
    "pv_string_alert": {"name": "PV String Alert", "object_id": "solid_ems_solid_pv_string_alert", "icon": "mdi:alert-circle"},
    "pv_string_imbalance_pct": {"name": "PV String Individual Deviation", "object_id": "solid_ems_solid_pv_string_individual_deviation", "unit": "%", "state_class": "measurement", "icon": "mdi:scale-unbalanced"},

    # Tempo
    "tempo": {"name": "Tempo", "object_id": "solid_ems_solid_tempo", "icon": "mdi:calendar-today"},
    "tempo_label": {"name": "Tempo Label", "object_id": "solid_ems_solid_tempo_label", "icon": "mdi:palette"},
    "tempo_tomorrow": {"name": "Tempo Tomorrow", "object_id": "solid_ems_solid_tempo_tomorrow", "icon": "mdi:calendar-arrow-right"},
    "tempo_tomorrow_label": {"name": "Tempo Tomorrow Label", "object_id": "solid_ems_solid_tempo_tomorrow_label", "icon": "mdi:palette-outline"},
}

# Alias exacts vus dans Home Assistant actuellement.
# Ceux-ci corrigent les entités à 0 créées par les anciennes découvertes MQTT.
ALIASES = [
    {"object_id": "panneaux_solaires_solid_ems_legacy_ecart_prevision_conso", "name": "Legacy Ecart Prevision Conso", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prevision_conso()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_ecart_prevision_conso_2", "name": "Legacy Ecart Prevision Conso 2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prevision_conso()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_estimated_autonomy", "name": "Legacy Estimated Autonomy", "unit": "h", "state_class": "measurement", "icon": "mdi:timer-sand", "template": tpl_autonomy()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_estimated_autonomy_2", "name": "Legacy Estimated Autonomy 2", "unit": "h", "state_class": "measurement", "icon": "mdi:timer-sand", "template": tpl_autonomy()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_estimated_battery_full", "name": "Legacy Estimated Battery Full", "unit": "h", "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_estimated_battery_full_2", "name": "Legacy Estimated Battery Full 2", "unit": "h", "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_forecast_load_gap", "name": "Legacy Forecast Load Gap", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prevision_conso()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_forecast_load_gap_2", "name": "Legacy Forecast Load Gap 2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:delta", "template": tpl_ecart_prevision_conso()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_habit_load_next_6h", "name": "Legacy Habit Load Next 6h", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-timeline-variant", "template": tpl_habit_load_next_6h_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_habit_load_next_6h_2", "name": "Legacy Habit Load Next 6h 2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-timeline-variant", "template": tpl_habit_load_next_6h_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_habit_load_now", "name": "Legacy Habit Load Now", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-bell-curve", "template": tpl_habit_load_now_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_habit_load_now_2", "name": "Legacy Habit Load Now 2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-bell-curve", "template": tpl_habit_load_now_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_pv_forecast", "name": "Legacy PV Forecast", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny", "template": tpl_pv_forecast_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_pv_forecast_2", "name": "Legacy PV Forecast 2", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny", "template": tpl_pv_forecast_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_pv_string_imbalance", "name": "Legacy PV String Imbalance", "unit": "%", "state_class": "measurement", "icon": "mdi:scale-unbalanced", "template": tpl_pv_string_imbalance()},
    {"object_id": "panneaux_solaires_solid_ems_legacy_pv_string_imbalance_2", "name": "Legacy PV String Imbalance 2", "unit": "%", "state_class": "measurement", "icon": "mdi:scale-unbalanced", "template": tpl_pv_string_imbalance()},
    {"object_id": "panneaux_solaires_solid_ems_solid_estimated_autonomy", "name": "SOLID Estimated Autonomy", "unit": "h", "state_class": "measurement", "icon": "mdi:timer-sand", "template": tpl_autonomy()},
    {"object_id": "panneaux_solaires_solid_ems_solid_estimated_battery_full", "name": "SOLID Estimated Battery Full", "unit": "h", "state_class": "measurement", "icon": "mdi:battery-clock", "template": tpl_batt_full()},
    {"object_id": "panneaux_solaires_solid_ems_solid_habit_load_next_6h", "name": "SOLID Habit Load Next 6h", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-timeline-variant", "template": tpl_habit_load_next_6h_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_solid_habit_load_now", "name": "SOLID Habit Load Now", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:chart-bell-curve", "template": tpl_habit_load_now_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_solid_pv_forecast", "name": "SOLID PV Forecast", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny", "template": tpl_pv_forecast_fallback()},
    {"object_id": "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation", "name": "SOLID PV String Individual Deviation", "unit": "%", "state_class": "measurement", "icon": "mdi:scale-unbalanced", "template": tpl_pv_string_imbalance()},
    {"object_id": "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation_2", "name": "SOLID PV String Individual Deviation 2", "unit": "%", "state_class": "measurement", "icon": "mdi:scale-unbalanced", "template": tpl_pv_string_imbalance()},
]


def _is_text_sensor(meta):
    if meta.get("unit"):
        return False
    if meta.get("device_class"):
        return False
    if meta.get("state_class"):
        return False
    return True


def _state_template(key, meta):
    if meta.get("template"):
        return meta["template"]
    if _is_text_sensor(meta):
        return tpl_txt(key)
    return tpl_num(key)


def _publish_config(mqtt, topic, config):
    mqtt.publish(topic, json.dumps(config, ensure_ascii=False), retain=True)
    print(f"MQTT Discovery published -> {topic}", flush=True)


def _build_config(key, meta):
    config = {
        "name": meta["name"],
        "object_id": meta["object_id"],
        "unique_id": meta["object_id"],
        "state_topic": STATE_TOPIC_DEFAULT,
        "value_template": _state_template(key, meta),
        "device": DEVICE,
        "icon": meta.get("icon"),
    }

    if meta.get("unit"):
        config["unit_of_measurement"] = meta["unit"]
    if meta.get("device_class"):
        config["device_class"] = meta["device_class"]
    if meta.get("state_class"):
        config["state_class"] = meta["state_class"]

    return config


def publish_discovery(mqtt, state_topic=STATE_TOPIC_DEFAULT, *args, **kwargs):
    print("MQTT Discovery published", flush=True)

    for key, meta in SENSORS.items():
        topic = f"homeassistant/sensor/solid/{key}/config"
        config = _build_config(key, meta)
        if state_topic != STATE_TOPIC_DEFAULT:
            config["state_topic"] = state_topic
        _publish_config(mqtt, topic, config)

    for meta in ALIASES:
        object_id = meta["object_id"]
        topic = f"homeassistant/sensor/{object_id}/config"
        config = _build_config("", meta)
        if state_topic != STATE_TOPIC_DEFAULT:
            config["state_topic"] = state_topic
        _publish_config(mqtt, topic, config)

    print("MQTT Discovery completed", flush=True)
