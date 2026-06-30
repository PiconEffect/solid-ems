import json


STATE_TOPIC_DEFAULT = "solid/state"
DISCOVERY_PREFIX_DEFAULT = "homeassistant"


DEVICE = {
    "identifiers": ["solid_ems"],
    "name": "SOLID EMS",
    "manufacturer": "SOLID EMS",
    "model": "Solis EMS Monitor",
}


def value_template(key, default="0"):
    return "{{ value_json." + key + " | default(" + default + ") }}"


def numeric_template(key):
    return "{{ value_json." + key + " | default(0) | float(0) }}"


def text_template(key):
    return "{{ value_json." + key + " | default('') }}"


NUMERIC_SENSORS = [
    # =========================================================================
    # Main power flow
    # =========================================================================
    {
        "key": "pv_power",
        "name": "PV Power",
        "object_id": "solid_pv_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
    },
    {
        "key": "battery_soc",
        "name": "Battery SOC",
        "object_id": "solid_battery_soc",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
        "icon": "mdi:battery",
    },
    {
        "key": "grid_power",
        "name": "Grid Power",
        "object_id": "solid_grid_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
    },
    {
        "key": "load_power",
        "name": "Load Power",
        "object_id": "solid_load_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
    },
    {
        "key": "battery_power",
        "name": "Battery Power",
        "object_id": "solid_battery_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-charging",
    },

    # =========================================================================
    # Energy counters
    # =========================================================================
    {
        "key": "daily_energy",
        "name": "Daily Energy",
        "object_id": "solid_daily_energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:counter",
    },
    {
        "key": "total_energy",
        "name": "Total Energy",
        "object_id": "solid_total_energy",
        "unit": "MWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "icon": "mdi:counter",
    },
    {
        "key": "inverter_temp",
        "name": "Inverter Temperature",
        "object_id": "solid_inverter_temp",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
    },

    # =========================================================================
    # PV strings / DC
    # =========================================================================
    {
        "key": "pv1_power",
        "name": "PV1 Power",
        "object_id": "solid_pv1_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-panel",
    },
    {
        "key": "pv2_power",
        "name": "PV2 Power",
        "object_id": "solid_pv2_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-panel",
    },
    {
        "key": "pv_total_dc_power",
        "name": "PV Total DC Power",
        "object_id": "solid_pv_total_dc_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power-variant",
    },

    # =========================================================================
    # Raw Solis values
    # =========================================================================
    {
        "key": "raw_power",
        "name": "Raw Power",
        "object_id": "solid_raw_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:flash",
    },
    {
        "key": "raw_pac",
        "name": "Raw PAC",
        "object_id": "solid_raw_pac",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:flash",
    },
    {
        "key": "raw_pow1_kw",
        "name": "Raw PV1 kW",
        "object_id": "solid_raw_pow1_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-panel",
    },
    {
        "key": "raw_pow2_kw",
        "name": "Raw PV2 kW",
        "object_id": "solid_raw_pow2_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-panel",
    },
    {
        "key": "raw_pv_dc_kw",
        "name": "Raw PV DC kW",
        "object_id": "solid_raw_pv_dc_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:solar-power",
    },
    {
        "key": "raw_family_load",
        "name": "Raw Family Load",
        "object_id": "solid_raw_family_load",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
    },
    {
        "key": "raw_total_load",
        "name": "Raw Total Load",
        "object_id": "solid_raw_total_load",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-lightning-bolt",
    },
    {
        "key": "raw_grid_psum",
        "name": "Raw Grid Psum",
        "object_id": "solid_raw_grid_psum",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:transmission-tower",
    },
    {
        "key": "raw_battery_power",
        "name": "Raw Battery Power",
        "object_id": "solid_raw_battery_power",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:battery-charging",
    },

    # =========================================================================
    # Tempo
    # =========================================================================
    {
        "key": "tempo",
        "name": "Tempo Today",
        "object_id": "solid_tempo",
        "unit": None,
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:calendar-today",
    },
    {
        "key": "tempo_tomorrow",
        "name": "Tempo Tomorrow",
        "object_id": "solid_tempo_tomorrow",
        "unit": None,
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:calendar-arrow-right",
    },

    # =========================================================================
    # Forecast / AI / supervision
    # =========================================================================
    {
        "key": "pv_forecast_kw",
        "name": "PV Forecast",
        "object_id": "solid_pv_forecast_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
    },
    {
        "key": "estimated_autonomy_h",
        "name": "Estimated Autonomy",
        "object_id": "solid_estimated_autonomy_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
    },
    {
        "key": "estimated_battery_full_h",
        "name": "Estimated Battery Full",
        "object_id": "solid_estimated_battery_full_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
    },
    {
        "key": "habit_load_now_kw",
        "name": "Habit Load Now",
        "object_id": "solid_habit_load_now_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-analytics",
    },
    {
        "key": "habit_load_next_6h_kw",
        "name": "Habit Load Next 6h",
        "object_id": "solid_habit_load_next_6h_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-clock",
    },
    {
        "key": "advice_priority",
        "name": "Advice Priority",
        "object_id": "solid_advice_priority",
        "unit": None,
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:numeric",
    },

    # =========================================================================
    # PV diagnostic
    # =========================================================================
    {
        "key": "pv_string_imbalance_pct",
        "name": "PV String Imbalance",
        "object_id": "solid_pv_string_imbalance_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
    },
]


CALCULATED_SENSORS = [
    # =========================================================================
    # Dashboard aliases / calculated helpers
    # =========================================================================
    {
        "name": "Autoconsumption",
        "object_id": "solid_autoconsumption_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:home-percent",
        "template": (
            "{% set pv = value_json.pv_power | float(0) %}"
            "{% set load = value_json.load_power | float(0) %}"
            "{% if pv > 0 %}"
            "{{ ([load, pv] | min / pv * 100) | round(1) }}"
            "{% else %}0{% endif %}"
        ),
    },
    {
        "name": "Autoconso",
        "object_id": "solid_autoconso_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:home-percent",
        "template": (
            "{% set pv = value_json.pv_power | float(0) %}"
            "{% set load = value_json.load_power | float(0) %}"
            "{% if pv > 0 %}"
            "{{ ([load, pv] | min / pv * 100) | round(1) }}"
            "{% else %}0{% endif %}"
        ),
    },
    {
        "name": "Forecast Load Gap",
        "object_id": "solid_forecast_load_gap_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": (
            "{{ ((value_json.habit_load_next_6h_kw | float(0)) "
            "- (value_json.pv_forecast_kw | float(0))) | round(2) }}"
        ),
    },
    {
        "name": "Ecart Prevision Conso",
        "object_id": "solid_ecart_prev_conso_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": (
            "{{ ((value_json.habit_load_next_6h_kw | float(0)) "
            "- (value_json.pv_forecast_kw | float(0))) | round(2) }}"
        ),
    },
    {
        "name": "Battery Full Calculated",
        "object_id": "solid_battery_full_calc_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": (
            "{% set soc = value_json.battery_soc | float(0) %}"
            "{% set p = value_json.battery_power | float(0) %}"
            "{% set cap = 30 %}"
            "{% if p > 0 and soc < 100 %}"
            "{{ (((100 - soc) / 100 * cap) / p) | round(2) }}"
            "{% else %}0{% endif %}"
        ),
    },
    {
        "name": "Batt Pleine",
        "object_id": "solid_batt_pleine_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": (
            "{% set soc = value_json.battery_soc | float(0) %}"
            "{% set p = value_json.battery_power | float(0) %}"
            "{% set cap = 30 %}"
            "{% if p > 0 and soc < 100 %}"
            "{{ (((100 - soc) / 100 * cap) / p) | round(2) }}"
            "{% else %}0{% endif %}"
        ),
    },
]


TEXT_SENSORS = [
    # =========================================================================
    # Tempo labels
    # =========================================================================
    {
        "key": "tempo_label",
        "name": "Tempo Label",
        "object_id": "solid_tempo_label",
        "icon": "mdi:calendar-today",
    },
    {
        "key": "tempo_tomorrow_label",
        "name": "Tempo Tomorrow Label",
        "object_id": "solid_tempo_tomorrow_label",
        "icon": "mdi:calendar-arrow-right",
    },

    # =========================================================================
    # AI supervision
    # =========================================================================
    {
        "key": "advice",
        "name": "AI Advice",
        "object_id": "solid_advice",
        "icon": "mdi:lightbulb-on-outline",
    },
    {
        "key": "advice",
        "name": "Supervision IA",
        "object_id": "solid_supervision_ia",
        "icon": "mdi:brain",
    },
    {
        "key": "prediction",
        "name": "AI Prediction",
        "object_id": "solid_prediction",
        "icon": "mdi:crystal-ball",
    },
    {
        "key": "energy_mode",
        "name": "Energy Mode",
        "object_id": "solid_energy_mode",
        "icon": "mdi:home-lightning-bolt",
    },
    {
        "key": "battery_strategy",
        "name": "Battery Strategy",
        "object_id": "solid_battery_strategy",
        "icon": "mdi:battery-heart",
    },
    {
        "key": "advice_confidence",
        "name": "Advice Confidence",
        "object_id": "solid_advice_confidence",
        "icon": "mdi:check-decagram",
    },

    # =========================================================================
    # PV diagnostic
    # =========================================================================
    {
        "key": "pv_string_status",
        "name": "PV String Status",
        "object_id": "solid_pv_string_status",
        "icon": "mdi:solar-panel",
    },
    {
        "key": "pv_string_alert",
        "name": "PV String Alert",
        "object_id": "solid_pv_string_alert",
        "icon": "mdi:alert-circle-outline",
    },
    {
        "key": "pv_string_alert",
        "name": "Diagnostic PV",
        "object_id": "solid_diag_pv",
        "icon": "mdi:solar-panel-large",
    },

    # =========================================================================
    # Timestamp
    # =========================================================================
    {
        "key": "timestamp",
        "name": "Timestamp",
        "object_id": "solid_timestamp",
        "icon": "mdi:clock-outline",
    },
]


def _publish_config(mqtt, topic, config):
    payload = json.dumps(config, ensure_ascii=False)

    mqtt.publish(
        topic,
        payload=payload,
        qos=0,
        retain=True,
    )

    print(f"MQTT Discovery published -> {topic}", flush=True)


def _numeric_sensor_config(sensor, state_topic):
    if sensor.get("template"):
        template = sensor["template"]
    else:
        template = numeric_template(sensor["key"])

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
    return {
        "name": sensor["name"],
        "object_id": sensor["object_id"],
        "unique_id": sensor["object_id"],
        "state_topic": state_topic,
        "value_template": text_template(sensor["key"]),
        "device": DEVICE,
        "icon": sensor.get("icon"),
    }


def publish_discovery(mqtt, state_topic=STATE_TOPIC_DEFAULT, *args, **kwargs):
    """
    Publie les configs MQTT Discovery Home Assistant.

    Compatible avec :
      publish_discovery(mqtt)
      publish_discovery(mqtt, state_topic)

    Correction racine :
      main.py peut appeler publish_discovery avec 2 arguments.
    """

    discovery_prefix = kwargs.get("discovery_prefix", DISCOVERY_PREFIX_DEFAULT)

    print(
        f"MQTT Discovery publish started state_topic={state_topic} prefix={discovery_prefix}",
        flush=True,
    )

    for sensor in NUMERIC_SENSORS:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _numeric_sensor_config(sensor, state_topic))

    for sensor in CALCULATED_SENSORS:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _numeric_sensor_config(sensor, state_topic))

    for sensor in TEXT_SENSORS:
        topic = f"{discovery_prefix}/sensor/{sensor['object_id']}/config"
        _publish_config(mqtt, topic, _text_sensor_config(sensor, state_topic))

    print("MQTT Discovery publish completed", flush=True)
