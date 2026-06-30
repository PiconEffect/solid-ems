import json


STATE_TOPIC_DEFAULT = "solid/state"
DISCOVERY_PREFIX_DEFAULT = "homeassistant"


DEVICE = {
    "identifiers": ["solid_ems"],
    "name": "SOLID EMS",
    "manufacturer": "SOLID EMS",
    "model": "Solis EMS Monitor",
}


# =============================================================================
# Templates helpers
# =============================================================================

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
        "{% if src > 0 %}"
        "{{ src | round(1) }}"
        "{% elif den > 0 %}"
        "{{ (((pv1 - pv2) | abs) / den * 100) | round(1) }}"
        "{% else %}0{% endif %}"
    )


# =============================================================================
# Numeric sensors
# =============================================================================

NUMERIC_SENSORS = [
    # -------------------------------------------------------------------------
    # Entités modernes principales
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Compteurs / état onduleur
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # PV strings / DC
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Raw Solis
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Forecast / IA raw source
    # -------------------------------------------------------------------------
    {
        "key": "pv_forecast_kw",
        "name": "PV Forecast Source",
        "object_id": "solid_pv_forecast_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
    },
    {
        "key": "habit_load_now_kw",
        "name": "Habit Load Now Source",
        "object_id": "solid_habit_load_now_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-analytics",
    },
    {
        "key": "habit_load_next_6h_kw",
        "name": "Habit Load Next 6h Source",
        "object_id": "solid_habit_load_next_6h_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-clock",
    },
    {
        "key": "estimated_battery_full_h",
        "name": "Estimated Battery Full Source",
        "object_id": "solid_estimated_battery_full_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
    },
    {
        "key": "estimated_autonomy_h",
        "name": "Estimated Autonomy Source",
        "object_id": "solid_estimated_autonomy_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
    },
    {
        "key": "pv_string_imbalance_pct",
        "name": "PV String Imbalance Source",
        "object_id": "solid_pv_string_imbalance_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
    },

    # -------------------------------------------------------------------------
    # Calculs modernes utiles
    # -------------------------------------------------------------------------
    {
        "name": "Autoconso",
        "object_id": "solid_autoconso_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:home-percent",
        "template": tpl_autoconso(),
    },
    {
        "name": "Autoconsumption",
        "object_id": "solid_autoconsumption_pct",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:home-percent",
        "template": tpl_autoconso(),
    },
    {
        "name": "Batt Pleine",
        "object_id": "solid_batt_pleine_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": tpl_batt_full(),
    },
    {
        "name": "Battery Full Calculated",
        "object_id": "solid_battery_full_calc_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": tpl_batt_full(),
    },
    {
        "name": "Estimated Autonomy Calculated",
        "object_id": "solid_estimated_autonomy_calc_h",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
        "template": tpl_autonomy(),
    },
    {
        "name": "PV Forecast Fallback",
        "object_id": "solid_pv_forecast_fallback_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },
    {
        "name": "Habit Load Now Fallback",
        "object_id": "solid_habit_load_now_fallback_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-analytics",
        "template": tpl_habit_load_now_fallback(),
    },
    {
        "name": "Habit Load Next 6h Fallback",
        "object_id": "solid_habit_load_next_6h_fallback_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-clock",
        "template": tpl_habit_load_next_6h_fallback(),
    },
    {
        "name": "Ecart Prevision Conso",
        "object_id": "solid_ecart_prev_conso_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": tpl_ecart_prevision_conso(),
    },
    {
        "name": "Forecast Load Gap",
        "object_id": "solid_forecast_load_gap_kw",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": tpl_ecart_prevision_conso(),
    },

    # -------------------------------------------------------------------------
    # Exact entity_id legacy listed by HA
    # -------------------------------------------------------------------------
    {
        "name": "Legacy Ecart Prevision Conso",
        "object_id": "panneaux_solaires_solid_ems_legacy_ecart_prevision_conso",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": tpl_ecart_prevision_conso(),
    },
    {
        "name": "Legacy Ecart Prevision Conso 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_ecart_prevision_conso_2",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": tpl_ecart_prevision_conso(),
    },
    {
        "name": "Legacy Estimated Autonomy",
        "object_id": "panneaux_solaires_solid_ems_legacy_estimated_autonomy",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
        "template": tpl_autonomy(),
    },
    {
        "name": "Legacy Estimated Autonomy 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_estimated_autonomy_2",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
        "template": tpl_autonomy(),
    },
    {
        "name": "Legacy Estimated Battery Full",
        "object_id": "panneaux_solaires_solid_ems_legacy_estimated_battery_full",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": tpl_batt_full(),
    },
    {
        "name": "Legacy Estimated Battery Full 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_estimated_battery_full_2",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": tpl_batt_full(),
    },
    {
        "name": "Legacy Forecast Load Gap",
        "object_id": "panneaux_solaires_solid_ems_legacy_forecast_load_gap",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": tpl_ecart_prevision_conso(),
    },
    {
        "name": "Legacy Forecast Load Gap 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_forecast_load_gap_2",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:delta",
        "template": tpl_ecart_prevision_conso(),
    },
    {
        "name": "Legacy Habit Load Next 6h",
        "object_id": "panneaux_solaires_solid_ems_legacy_habit_load_next_6h",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-clock",
        "template": tpl_habit_load_next_6h_fallback(),
    },
    {
        "name": "Legacy Habit Load Next 6h 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_habit_load_next_6h_2",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-clock",
        "template": tpl_habit_load_next_6h_fallback(),
    },
    {
        "name": "Legacy Habit Load Now",
        "object_id": "panneaux_solaires_solid_ems_legacy_habit_load_now",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-analytics",
        "template": tpl_habit_load_now_fallback(),
    },
    {
        "name": "Legacy Habit Load Now 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_habit_load_now_2",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-analytics",
        "template": tpl_habit_load_now_fallback(),
    },
    {
        "name": "Legacy PV Forecast",
        "object_id": "panneaux_solaires_solid_ems_legacy_pv_forecast",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },
    {
        "name": "Legacy PV Forecast 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_pv_forecast_2",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },
    {
        "name": "Legacy PV String Imbalance",
        "object_id": "panneaux_solaires_solid_ems_legacy_pv_string_imbalance",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
        "template": tpl_pv_string_imbalance(),
    },
    {
        "name": "Legacy PV String Imbalance 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_pv_string_imbalance_2",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
        "template": tpl_pv_string_imbalance(),
    },
    {
        "name": "SOLID Estimated Autonomy",
        "object_id": "panneaux_solaires_solid_ems_solid_estimated_autonomy",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
        "template": tpl_autonomy(),
    },
    {
        "name": "SOLID Estimated Battery Full",
        "object_id": "panneaux_solaires_solid_ems_solid_estimated_battery_full",
        "unit": "h",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:battery-clock",
        "template": tpl_batt_full(),
    },
    {
        "name": "SOLID Habit Load Next 6h",
        "object_id": "panneaux_solaires_solid_ems_solid_habit_load_next_6h",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-clock",
        "template": tpl_habit_load_next_6h_fallback(),
    },
    {
        "name": "SOLID Habit Load Now",
        "object_id": "panneaux_solaires_solid_ems_solid_habit_load_now",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:home-analytics",
        "template": tpl_habit_load_now_fallback(),
    },
    {
        "name": "SOLID PV Forecast",
        "object_id": "panneaux_solaires_solid_ems_solid_pv_forecast",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },
    {
        "name": "SOLID PV String Individual Deviation",
        "object_id": "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
        "template": tpl_pv_string_imbalance(),
    },
    {
        "name": "SOLID PV String Individual Deviation 2",
        "object_id": "panneaux_solaires_solid_ems_solid_pv_string_individual_deviation_2",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:solar-panel-large",
        "template": tpl_pv_string_imbalance(),
    },
    {
        "name": "SOLID EMS PV Forecast",
        "object_id": "solid_ems_solid_pv_forecast",
        "unit": "kW",
        "device_class": "power",
        "state_class": "measurement",
        "icon": "mdi:weather-sunny",
        "template": tpl_pv_forecast_fallback(),
    },
]


# =============================================================================
# Text sensors
# =============================================================================

TEXT_SENSORS = [
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
        "key": "advice",
        "name": "Legacy AI Advice",
        "object_id": "panneaux_solaires_solid_ems_legacy_ai_advice",
        "icon": "mdi:brain",
    },
    {
        "key": "advice",
        "name": "Legacy AI Advice 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_ai_advice_2",
        "icon": "mdi:brain",
    },
    {
        "key": "prediction",
        "name": "AI Prediction",
        "object_id": "solid_prediction",
        "icon": "mdi:crystal-ball",
    },
    {
        "key": "prediction",
        "name": "Legacy AI Prediction",
        "object_id": "panneaux_solaires_solid_ems_legacy_ai_prediction",
        "icon": "mdi:crystal-ball",
    },
    {
        "key": "prediction",
        "name": "Legacy AI Prediction 2",
        "object_id": "panneaux_solaires_solid_ems_legacy_ai_prediction_2",
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
        "key": "battery_strategy",
        "name": "Battery Strategy",
        "object_id": "panneaux_solaires_solid_ems_solid_battery_strategy",
        "icon": "mdi:battery-heart",
    },
    {
        "key": "advice_confidence",
        "name": "Advice Confidence",
        "object_id": "solid_advice_confidence",
        "icon": "mdi:check-decagram",
    },
    {
        "key": "pv_string_status",
        "name": "PV String Status",
        "object_id": "solid_pv_string_status",
        "icon": "mdi:solar-panel",
    },
    {
        "key": "pv_string_status",
        "name": "PV String Status",
        "object_id": "panneaux_solaires_solid_ems_solid_pv_string_status",
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
    {
        "key": "timestamp",
        "name": "Timestamp",
        "object_id": "solid_timestamp",
        "icon": "mdi:clock-outline",
    },
]


# =============================================================================
# Discovery builders
# =============================================================================

def _dedupe(items):
    result = {}
    for item in items:
        result[item["object_id"]] = item
    return list(result.values())


def _publish_config(mqtt, topic, config):
    mqtt.publish(
        topic,
        payload=json.dumps(config, ensure_ascii=False),
        qos=0,
        retain=True,
    )
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
    """
    Publie toutes les configs MQTT Discovery Home Assistant.

    Signature compatible avec :
      publish_discovery(mqtt)
      publish_discovery(mqtt, state_topic)
    """

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
