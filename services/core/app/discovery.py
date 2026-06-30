import json

STATE_TOPIC_DEFAULT = "solid/state"
DISCOVERY_PREFIX_DEFAULT = "homeassistant"

DEVICE = {
    "identifiers": ["solid_ems"],
    "name": "SOLID EMS",
    "manufacturer": "SOLID EMS",
    "model": "Solis EMS Monitor",
}


def mqtt_template_number(key):
    return "{{ value_json." + key + " | default(0) | float(0) }}"


def mqtt_template_text(key):
    return "{{ value_json." + key + " | default('') }}"


BASE_NUMERIC_SENSORS = [
    # Main flow
    {"key": "pv_power", "name": "PV Power", "object_id": "solid_pv_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "battery_soc", "name": "Battery SOC", "object_id": "solid_battery_soc", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery"},
    {"key": "grid_power", "name": "Grid Power", "object_id": "solid_grid_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    {"key": "load_power", "name": "Load Power", "object_id": "solid_load_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    {"key": "battery_power", "name": "Battery Power", "object_id": "solid_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},
    # Energy / inverter
    {"key": "daily_energy", "name": "Daily Energy", "object_id": "solid_daily_energy", "unit": "kWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:counter"},
    {"key": "total_energy", "name": "Total Energy", "object_id": "solid_total_energy", "unit": "MWh", "device_class": "energy", "state_class": "total_increasing", "icon": "mdi:counter"},
    {"key": "inverter_temp", "name": "Inverter Temperature", "object_id": "solid_inverter_temp", "unit": "°C", "device_class": "temperature", "state_class": "measurement", "icon": "mdi:thermometer"},
    # PV string / DC
    {"key": "pv1_power", "name": "PV1 Power", "object_id": "solid_pv1_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    {"key": "pv2_power", "name": "PV2 Power", "object_id": "solid_pv2_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    {"key": "pv_total_dc_power", "name": "PV Total DC Power", "object_id": "solid_pv_total_dc_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power-variant"},
    # Raw values
    {"key": "raw_power", "name": "Raw Power", "object_id": "solid_raw_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:flash"},
    {"key": "raw_pac", "name": "Raw PAC", "object_id": "solid_raw_pac", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:flash"},
    {"key": "raw_pow1_kw", "name": "Raw PV1 kW", "object_id": "solid_raw_pow1_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    {"key": "raw_pow2_kw", "name": "Raw PV2 kW", "object_id": "solid_raw_pow2_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-panel"},
    {"key": "raw_pv_dc_kw", "name": "Raw PV DC kW", "object_id": "solid_raw_pv_dc_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:solar-power"},
    {"key": "raw_family_load", "name": "Raw Family Load", "object_id": "solid_raw_family_load", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    {"key": "raw_total_load", "name": "Raw Total Load", "object_id": "solid_raw_total_load", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-lightning-bolt"},
    {"key": "raw_grid_psum", "name": "Raw Grid Psum", "object_id": "solid_raw_grid_psum", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:transmission-tower"},
    {"key": "raw_battery_power", "name": "Raw Battery Power", "object_id": "solid_raw_battery_power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},
    # Tempo numeric
    {"key": "tempo", "name": "Tempo Today", "object_id": "solid_tempo", "unit": None, "device_class": None, "state_class": "measurement", "icon": "mdi:calendar-today"},
    {"key": "tempo_tomorrow", "name": "Tempo Tomorrow", "object_id": "solid_tempo_tomorrow", "unit": None, "device_class": None, "state_class": "measurement", "icon": "mdi:calendar-arrow-right"},
    # IA / forecast / habits
    {"key": "pv_forecast_kw", "name": "PV Forecast", "object_id": "solid_pv_forecast_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny"},
    {"key": "estimated_autonomy_h", "name": "Estimated Autonomy", "object_id": "solid_estimated_autonomy_h", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:timer-outline"},
    {"key": "estimated_battery_full_h", "name": "Estimated Battery Full", "object_id": "solid_estimated_battery_full_h", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock"},
    {"key": "habit_load_now_kw", "name": "Habit Load Now", "object_id": "solid_habit_load_now_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-analytics"},
    {"key": "habit_load_next_6h_kw", "name": "Habit Load Next 6h", "object_id": "solid_habit_load_next_6h_kw", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:home-clock"},
    {"key": "advice_priority", "name": "Advice Priority", "object_id": "solid_advice_priority", "unit": None, "device_class": None, "state_class": "measurement", "icon": "mdi:numeric"},
    # PV diagnostic
    {"key": "pv_string_imbalance_pct", "name": "PV String Imbalance", "object_id": "solid_pv_string_imbalance_pct", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:solar-panel-large"},
]

BASE_TEXT_SENSORS = [
    {"key": "tempo_label", "name": "Tempo Label", "object_id": "solid_tempo_label", "icon": "mdi:calendar-today"},
    {"key": "tempo_tomorrow_label", "name": "Tempo Tomorrow Label", "object_id": "solid_tempo_tomorrow_label", "icon": "mdi:calendar-arrow-right"},
    {"key": "advice", "name": "AI Advice", "object_id": "solid_advice", "icon": "mdi:lightbulb-on-outline"},
    {"key": "prediction", "name": "AI Prediction", "object_id": "solid_prediction", "icon": "mdi:crystal-ball"},
    {"key": "energy_mode", "name": "Energy Mode", "object_id": "solid_energy_mode", "icon": "mdi:home-lightning-bolt"},
    {"key": "battery_strategy", "name": "Battery Strategy", "object_id": "solid_battery_strategy", "icon": "mdi:battery-heart"},
    {"key": "advice_confidence", "name": "Advice Confidence", "object_id": "solid_advice_confidence", "icon": "mdi:check-decagram"},
    {"key": "pv_string_status", "name": "PV String Status", "object_id": "solid_pv_string_status", "icon": "mdi:solar-panel"},
    {"key": "pv_string_alert", "name": "PV String Alert", "object_id": "solid_pv_string_alert", "icon": "mdi:alert-circle-outline"},
    {"key": "timestamp", "name": "Timestamp", "object_id": "solid_timestamp", "icon": "mdi:clock-outline"},
]

CALCULATED_NUMERIC_SENSORS = [
    {
        "name": "Autoconsumption",
        "object_id": "solid_autoconsumption_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:home-percent",
        "template": "{% set pv = value_json.pv_power | float(0) %}{% set load = value_json.load_power | float(0) %}{% if pv > 0 %}{{ ([load, pv] | min / pv * 100) | round(1) }}{% else %}0{% endif %}",
    },
    {
        "name": "Autoconso",
        "object_id": "solid_autoconso_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:home-percent",
        "template": "{% set pv = value_json.pv_power | float(0) %}{% set load = value_json.load_power | float(0) %}{% if pv > 0 %}{{ ([load, pv] | min / pv * 100) | round(1) }}{% else %}0{% endif %}",
    },
    {
        "name": "Forecast Load Gap",
        "object_id": "solid_forecast_load_gap_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": "{{ ((value_json.habit_load_next_6h_kw | float(0)) - (value_json.pv_forecast_kw | float(0))) | round(2) }}",
    },
    {
        "name": "Ecart Prevision Conso",
        "object_id": "solid_ecart_prev_conso_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": "{{ ((value_json.habit_load_next_6h_kw | float(0)) - (value_json.pv_forecast_kw | float(0))) | round(2) }}",
    },
    {
        "name": "Battery Full Calculated",
        "object_id": "solid_battery_full_calc_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": "{% set soc = value_json.battery_soc | float(0) %}{% set p = value_json.battery_power | float(0) %}{% set cap = 30 %}{% if p > 0 and soc < 100 %}{{ (((100 - soc) / 100 * cap) / p) | round(2) }}{% else %}0{% endif %}",
    },
    {
        "name": "Batt Pleine",
        "object_id": "solid_batt_pleine_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": "{% set soc = value_json.battery_soc | float(0) %}{% set p = value_json.battery_power | float(0) %}{% set cap = 30 %}{% if p > 0 and soc < 100 %}{{ (((100 - soc) / 100 * cap) / p) | round(2) }}{% else %}0{% endif %}",
    },
]

DASHBOARD_TEXT_ALIASES = [
    {"key": "advice", "name": "Supervision IA", "object_id": "solid_supervision_ia", "icon": "mdi:brain"},
    {"key": "pv_string_alert", "name": "Diagnostic PV", "object_id": "solid_diag_pv", "icon": "mdi:solar-panel-large"},
]

MANUAL_NUMERIC_ALIASES = [
    # Exact entity ids found in HomeAssistant/DashBoard*.yaml
    {"source_key": "battery_soc", "object_id": "solid_ems_solid_battery_soc", "name": "SOLID Battery SOC", "unit": "%", "device_class": "battery", "state_class": "measurement", "icon": "mdi:battery"},
    {"source_key": "battery_power", "object_id": "solid_ems_solid_battery_power", "name": "SOLID Battery Power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},
    {"source_key": "pv_forecast_kw", "object_id": "solid_ems_solid_pv_forecast", "name": "SOLID PV Forecast", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:weather-sunny"},
    {"source_key": "pv_string_imbalance_pct", "object_id": "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation", "name": "SOLID PV String Individual Deviation", "unit": "%", "device_class": None, "state_class": "measurement", "icon": "mdi:solar-panel-large"},
    {"source_key": "raw_battery_power", "object_id": "panneaux_solaires_solid_ems_solid_raw_battery_power", "name": "SOLID Raw Battery Power", "unit": "kW", "device_class": "power", "state_class": "measurement", "icon": "mdi:battery-charging"},
    # This dashboard entity used to be a source value, but source is currently 0. Use calculated template for useful value.
    {"source_key": None, "object_id": "panneaux_solaires_solid_ems_solid_estimated_battery_full", "name": "SOLID Estimated Battery Full", "unit": "h", "device_class": None, "state_class": "measurement", "icon": "mdi:battery-clock", "template": "{% set soc = value_json.battery_soc | float(0) %}{% set p = value_json.battery_power | float(0) %}{% set cap = 30 %}{% if p > 0 and soc < 100 %}{{ (((100 - soc) / 100 * cap) / p) | round(2) }}{% else %}0{% endif %}"},
]

MANUAL_TEXT_ALIASES = [
    {"source_key": "battery_strategy", "object_id": "panneaux_solaires_solid_ems_solid_battery_strategy", "name": "SOLID Battery Strategy", "icon": "mdi:battery-heart"},
    {"source_key": "pv_string_status", "object_id": "panneaux_solaires_solid_ems_solid_pv_string_status", "name": "SOLID PV String Status", "icon": "mdi:solar-panel"},
]


def _legacy_numeric_aliases():
    aliases = []
    all_numeric = BASE_NUMERIC_SENSORS + CALCULATED_NUMERIC_SENSORS
    for sensor in all_numeric:
        for prefix in ["solid_ems_", "panneaux_solaires_solid_ems_"]:
            alias = dict(sensor)
            alias["object_id"] = prefix + sensor["object_id"]
            alias["name"] = "Legacy " + sensor["name"]
            aliases.append(alias)
    return aliases


def _legacy_text_aliases():
    aliases = []
    all_text = BASE_TEXT_SENSORS + DASHBOARD_TEXT_ALIASES
    for sensor in all_text:
        for prefix in ["solid_ems_", "panneaux_solaires_solid_ems_"]:
            alias = dict(sensor)
            alias["object_id"] = prefix + sensor["object_id"]
            alias["name"] = "Legacy " + sensor["name"]
            aliases.append(alias)
    return aliases


def _dedupe_by_object_id(items):
    seen = {}
    for item in items:
        seen[item["object_id"]] = item
    return list(seen.values())


def _publish_config(mqtt, topic, config):
    mqtt.publish(topic, payload=json.dumps(config, ensure_ascii=False), qos=0, retain=True)
    print(f"MQTT Discovery published -> {topic}", flush=True)


def _numeric_sensor_config(sensor, state_topic):
    if sensor.get("template"):
        template = sensor["template"]
    else:
        key = sensor.get("key") or sensor.get("source_key")
        template = mqtt_template_number(key)

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


def _text_sensor_config(sensor, state_topic):
    key = sensor.get("key") or sensor.get("source_key")
    return {
        "name": sensor["name"],
        "object_id": sensor["object_id"],
        "unique_id": sensor["object_id"],
        "state_topic": state_topic,
        "value_template": mqtt_template_text(key),
        "device": DEVICE,
        "icon": sensor.get("icon"),
    }


def publish_discovery(mqtt, state_topic=STATE_TOPIC_DEFAULT, *args, **kwargs):
    """
    Publie toutes les configs MQTT Discovery Home Assistant.

    Signature compatible avec main.py :
      publish_discovery(mqtt)
      publish_discovery(mqtt, state_topic)
    """
    discovery_prefix = kwargs.get("discovery_prefix", DISCOVERY_PREFIX_DEFAULT)
    print(f"MQTT Discovery publish started state_topic={state_topic} prefix={discovery_prefix}", flush=True)

    numeric_sensors = _dedupe_by_object_id(
        BASE_NUMERIC_SENSORS
        + CALCULATED_NUMERIC_SENSORS
        + DASHBOARD_TEXT_ALIASES[:0]
        + MANUAL_NUMERIC_ALIASES
        + _legacy_numeric_aliases()
    )
    text_sensors = _dedupe_by_object_id(
        BASE_TEXT_SENSORS
        + DASHBOARD_TEXT_ALIASES
        + MANUAL_TEXT_ALIASES
        + _legacy_text_aliases()
    )

    for sensor in numeric_sensors:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _numeric_sensor_config(sensor, state_topic))

    for sensor in text_sensors:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _text_sensor_config(sensor, state_topic))

    print(
        f"MQTT Discovery publish completed numeric={len(numeric_sensors)} text={len(text_sensors)}",
        flush=True,
    )
