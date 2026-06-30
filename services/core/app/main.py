import json
import os
import time
from datetime import datetime

import paho.mqtt.client as mqtt

from solis_client import SolisClient
from battery_control import BatteryControl


MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

STATE_TOPIC = "solid/state"
BATTERY_COMMAND_TOPIC = "solid/command/battery_discharge_inhibit"


# -------------------------------------------------------------------
# Optional discovery module compatibility layer
# -------------------------------------------------------------------
try:
    import discovery as discovery_module
except Exception as error:
    discovery_module = None
    print("Discovery module unavailable:", error, flush=True)


# -------------------------------------------------------------------
# Optional tempo module compatibility layer
# -------------------------------------------------------------------
try:
    import tempo as tempo_module
except Exception as error:
    tempo_module = None
    print("Tempo module unavailable:", error, flush=True)


# -------------------------------------------------------------------
# Optional AI engine module compatibility layer
# -------------------------------------------------------------------
try:
    import ai_engine as ai_engine_module
except Exception as error:
    ai_engine_module = None
    print("AI engine module unavailable:", error, flush=True)


def publish_discovery_safe(mqtt_client):
    if discovery_module is None:
        print("MQTT Discovery skipped: discovery module not available", flush=True)
        return

    discovery_function_names = [
        "publish_discovery",
        "publish_mqtt_discovery",
        "publish_all_discovery",
        "publish_homeassistant_discovery",
    ]

    for function_name in discovery_function_names:
        function = getattr(discovery_module, function_name, None)

        if callable(function):
            try:
                function(mqtt_client)
                print("MQTT Discovery published", flush=True)
                return
            except TypeError:
                try:
                    function(mqtt_client, STATE_TOPIC)
                    print("MQTT Discovery published", flush=True)
                    return
                except Exception as error:
                    print(
                        f"MQTT Discovery function {function_name} failed:",
                        error,
                        flush=True,
                    )
                    return
            except Exception as error:
                print(
                    f"MQTT Discovery function {function_name} failed:",
                    error,
                    flush=True,
                )
                return

    print("MQTT Discovery skipped: no compatible function found", flush=True)


def get_tempo_data_safe():
    default = {
        "tempo": 1,
        "tempo_label": "Bleu",
        "tempo_tomorrow": 1,
        "tempo_tomorrow_label": "Bleu",
    }

    if tempo_module is None:
        return default

    try:
        if hasattr(tempo_module, "get_tempo_data"):
            data = tempo_module.get_tempo_data()
            if isinstance(data, dict):
                return {**default, **data}

        if hasattr(tempo_module, "get_tempo"):
            data = tempo_module.get_tempo()
            if isinstance(data, dict):
                return {**default, **data}

        if hasattr(tempo_module, "TempoClient"):
            client = tempo_module.TempoClient()

            for method_name in ["get_data", "get_tempo_data", "get_tempo"]:
                method = getattr(client, method_name, None)

                if callable(method):
                    data = method()
                    if isinstance(data, dict):
                        return {**default, **data}

    except Exception as error:
        print("Tempo error:", error, flush=True)

    return default


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def compute_pv_string_diagnostic(state):
    """
    Diagnostic PV robuste calculé directement depuis PV1/PV2.

    Objectif :
    - conserver toutes les fonctions existantes
    - ne remplacer le diagnostic IA que s'il est absent, UNKNOWN ou indisponible
    - publier un diagnostic PV exploitable si pv1_power/pv2_power existent
    """

    pv1 = _safe_float(state.get("pv1_power", state.get("raw_pow1_kw", 0.0)))
    pv2 = _safe_float(state.get("pv2_power", state.get("raw_pow2_kw", 0.0)))
    pv_dc = _safe_float(state.get("pv_total_dc_power", state.get("raw_pv_dc_kw", 0.0)))
    pv_ac = _safe_float(state.get("pv_power", state.get("raw_pac", 0.0)))

    total_strings = pv1 + pv2
    total_ref = max(total_strings, pv_dc, pv_ac)

    if total_ref < 0.5:
        return {
            "pv_string_status": "LOW_LIGHT",
            "pv_string_alert": "Production trop faible pour diagnostiquer les strings PV",
            "pv_string_imbalance_pct": 0.0,
        }

    if total_strings <= 0:
        return {
            "pv_string_status": "UNKNOWN",
            "pv_string_alert": "Diagnostic strings PV indisponible : données PV1/PV2 absentes",
            "pv_string_imbalance_pct": 0.0,
        }

    imbalance_pct = abs(pv1 - pv2) / total_strings * 100.0

    if imbalance_pct < 25:
        status = "OK"
        alert = f"Strings PV équilibrés : écart {imbalance_pct:.1f} %"
    elif imbalance_pct < 40:
        status = "WATCH"
        alert = f"Écart strings PV à surveiller : {imbalance_pct:.1f} %"
    elif imbalance_pct < 60:
        status = "WARNING"
        alert = f"Écart strings PV élevé : {imbalance_pct:.1f} %"
    else:
        status = "CRITICAL"
        alert = f"Déséquilibre strings PV critique : {imbalance_pct:.1f} %"

    return {
        "pv_string_status": status,
        "pv_string_alert": alert,
        "pv_string_imbalance_pct": round(imbalance_pct, 1),
    }


def get_ai_data_safe(solis_data, tempo_data):
    default = {
        "advice": "Autoconsommation stable. Surveiller PV, batterie et réseau.",
        "pv_forecast_kw": 0.0,
        "prediction": "Autoconsommation stable.",
        "energy_mode": "Autoconsommation stable",
        "battery_strategy": "Préserver la batterie",
        "estimated_autonomy_h": 0.0,
        "estimated_battery_full_h": 0.0,
        "habit_load_now_kw": 0.0,
        "habit_load_next_6h_kw": 0.0,
        "advice_priority": 5,
        "advice_confidence": "medium",
        "pv_string_status": "UNKNOWN",
        "pv_string_alert": "Diagnostic strings indisponible",
        "pv_string_imbalance_pct": 0.0,
    }

    if ai_engine_module is None:
        return default

    try:
        possible_class_names = [
            "AIEnergyEngine",
            "SolidAIEngine",
            "AIEngine",
            "EnergyAIEngine",
        ]

        engine = None

        for class_name in possible_class_names:
            candidate = getattr(ai_engine_module, class_name, None)

            if candidate:
                try:
                    engine = candidate()
                    break
                except Exception:
                    continue

        if engine is None:
            for function_name in [
                "analyze",
                "process",
                "evaluate",
                "get_ai_data",
                "get_advice",
            ]:
                function = getattr(ai_engine_module, function_name, None)

                if callable(function):
                    data = function(solis_data, tempo_data)

                    if isinstance(data, dict):
                        return {**default, **data}

                    return default

            return default

        for method_name in [
            "analyze",
            "process",
            "evaluate",
            "get_ai_data",
            "get_advice",
            "run",
        ]:
            method = getattr(engine, method_name, None)

            if callable(method):
                try:
                    data = method(solis_data, tempo_data)
                except TypeError:
                    data = method(solis_data)

                if isinstance(data, dict):
                    return {**default, **data}

                return default

    except Exception as error:
        print("AI engine error:", error, flush=True)

    return default


def normalize_state(solis_data, tempo_data, ai_data):
    state = {}

    if isinstance(solis_data, dict):
        state.update(solis_data)

    if isinstance(tempo_data, dict):
        state.update(tempo_data)

    if isinstance(ai_data, dict):
        state.update(ai_data)

    # -------------------------------------------------------------------
    # Diagnostic PV fallback robuste.
    #
    # On conserve le diagnostic IA s'il est valide.
    # On remplace uniquement les valeurs absentes, UNKNOWN, indisponibles
    # ou à 0 alors que PV1/PV2 sont disponibles.
    # -------------------------------------------------------------------
    pv_diag = compute_pv_string_diagnostic(state)

    current_status = str(state.get("pv_string_status") or "").upper()
    current_alert = str(state.get("pv_string_alert") or "")
    current_imbalance = _safe_float(state.get("pv_string_imbalance_pct"), 0.0)

    if (
        current_status in ["", "UNKNOWN", "NONE"]
        or "indisponible" in current_alert.lower()
        or current_imbalance <= 0.0
    ):
        state.update(pv_diag)

    numeric_defaults = {
        "pv_power": 0.0,
        "battery_soc": 0.0,
        "grid_power": 0.0,
        "load_power": 0.0,
        "battery_power": 0.0,
        "daily_energy": 0.0,
        "total_energy": 0.0,
        "inverter_temp": 0.0,
        "pv1_power": 0.0,
        "pv2_power": 0.0,
        "pv_total_dc_power": 0.0,
        "raw_power": 0.0,
        "raw_pac": 0.0,
        "raw_pow1_kw": 0.0,
        "raw_pow2_kw": 0.0,
        "raw_pv_dc_kw": 0.0,
        "raw_family_load": 0.0,
        "raw_total_load": 0.0,
        "raw_grid_psum": 0.0,
        "raw_battery_power": 0.0,
        "pv_forecast_kw": 0.0,
        "estimated_autonomy_h": 0.0,
        "estimated_battery_full_h": 0.0,
        "habit_load_now_kw": 0.0,
        "habit_load_next_6h_kw": 0.0,
        "advice_priority": 5,
        "pv_string_imbalance_pct": 0.0,
    }

    text_defaults = {
        "advice": "Autoconsommation stable. Surveiller PV, batterie et réseau.",
        "tempo_label": "Bleu",
        "tempo_tomorrow_label": "Bleu",
        "prediction": "Autoconsommation stable.",
        "energy_mode": "Autoconsommation stable",
        "battery_strategy": "Préserver la batterie",
        "advice_confidence": "medium",
        "pv_string_status": "UNKNOWN",
        "pv_string_alert": "Diagnostic strings indisponible",
    }

    integer_defaults = {
        "tempo": 1,
        "tempo_tomorrow": 1,
    }

    for key, value in numeric_defaults.items():
        if key not in state or state[key] is None:
            state[key] = value

    for key, value in text_defaults.items():
        if key not in state or state[key] is None:
            state[key] = value

    for key, value in integer_defaults.items():
        if key not in state or state[key] is None:
            state[key] = value

    state["timestamp"] = datetime.now().isoformat(timespec="seconds")

    return state


def publish_state(mqtt_client, state):
    payload = json.dumps(state, ensure_ascii=False)

    mqtt_client.publish(
        STATE_TOPIC,
        payload,
        retain=True,
    )

    print(f"MQTT publish -> {STATE_TOPIC}: {payload}", flush=True)
    print("Published state:", state, flush=True)


def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected", flush=True)

        client.subscribe(BATTERY_COMMAND_TOPIC)
        print(f"MQTT subscribed -> {BATTERY_COMMAND_TOPIC}", flush=True)

    else:
        print(f"MQTT connection failed rc={rc}", flush=True)


def create_battery_command_handler(battery_control):
    def on_battery_command_message(client, userdata, message):
        try:
            payload_raw = message.payload.decode("utf-8")
            print(f"MQTT command <- {message.topic}: {payload_raw}", flush=True)

            payload = json.loads(payload_raw)
            battery_control.handle_command(payload)

        except Exception as error:
            print("ERROR handling battery command:", error, flush=True)

    return on_battery_command_message


def main():
    print("SOLID EMS starting...", flush=True)
    print(f"MQTT broker: {MQTT_HOST}:{MQTT_PORT}", flush=True)
    print(f"Polling interval: {POLL_INTERVAL}s", flush=True)

    solis = SolisClient()

    battery_control = BatteryControl(
        inverter_sn=getattr(solis, "inverter_sn", None)
    )

    mqtt_client = mqtt.Client(client_id="solid-core")
    mqtt_client.on_connect = on_mqtt_connect

    mqtt_client.message_callback_add(
        BATTERY_COMMAND_TOPIC,
        create_battery_command_handler(battery_control),
    )

    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start()

    publish_discovery_safe(mqtt_client)

    last_state = None

    while True:
        try:
            solis_data = solis.get_data()

            if getattr(solis, "inverter_sn", None):
                battery_control.update_inverter_sn(solis.inverter_sn)

            if not solis_data:
                print("No Solis data received, using last known values", flush=True)

                if last_state:
                    state = dict(last_state)
                    state["timestamp"] = datetime.now().isoformat(timespec="seconds")
                    publish_state(mqtt_client, state)
                else:
                    tempo_data = get_tempo_data_safe()
                    ai_data = get_ai_data_safe({}, tempo_data)
                    state = normalize_state({}, tempo_data, ai_data)
                    publish_state(mqtt_client, state)

                time.sleep(POLL_INTERVAL)
                continue

            tempo_data = get_tempo_data_safe()
            ai_data = get_ai_data_safe(solis_data, tempo_data)

            state = normalize_state(solis_data, tempo_data, ai_data)

            last_state = state

            print("Solis data OK", flush=True)
            publish_state(mqtt_client, state)

        except Exception as error:
            print("ERROR MAIN LOOP:", error, flush=True)

            if last_state:
                try:
                    state = dict(last_state)
                    state["timestamp"] = datetime.now().isoformat(timespec="seconds")
                    publish_state(mqtt_client, state)
                except Exception as publish_error:
                    print("ERROR publishing last known state:", publish_error, flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
