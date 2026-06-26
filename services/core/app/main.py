import os
import time

from ai_engine import AiEngine
from discovery importisponible",from discovery import publish_discovery
    "estimated_autonomy_h": 0.0,
    "estimated_battery_full_h": 0.0,
    "habit_load_now_kw": 0.0,
    "habit_load_next_6h_kw": 0.0,
    "advice_priority": 0,
    "advice_confidence": "low",
    "pv_string_status": "UNKNOWN",
    "pv_string_alert": "Diagnostic strings PV indisponible",
    "pv_string_imbalance_pct": 0.0,
}


def merge_with_defaults(data, defaults):
    result = defaults.copy()

    if isinstance(data, dict):
        for key, value in data.items():
            result[key] = value

    return result


def main():
    print("SOLID EMS starting...", flush=True)

    poll_interval = int(os.getenv("POLL_INTERVAL", "30"))

    mqtt = MqttClient()
    solis = SolisClient()
    ai = AiEngine()

    publish_discovery(mqtt)

    print("MQTT Discovery published", flush=True)
    print(f"Polling interval: {poll_interval}s", flush=True)

    last_good_solis_data = DEFAULT_SOLIS_DATA.copy()

    while True:
        try:
            solis_data = solis.get_data()

            if solis_data:
                last_good_solis_data = merge_with_defaults(
                    solis_data,
                    DEFAULT_SOLIS_DATA,
                )
                print("Solis data OK", flush=True)
            else:
                print("No Solis data received, using last known values", flush=True)

            safe_solis_data = merge_with_defaults(
                last_good_solis_data,
                DEFAULT_SOLIS_DATA,
            )

            try:
                ai_data = ai.analyze(safe_solis_data)
            except Exception as error:
                print("AI analyze error:", error, flush=True)
                ai_data = DEFAULT_AI_DATA.copy()

            safe_ai_data = merge_with_defaults(
                ai_data,
                DEFAULT_AI_DATA,
            )

            payload = {
                **safe_solis_data,
                **safe_ai_data,
            }

            mqtt.publish("solid/state", payload, retain=True)

            print("MQTT publish -> solid/state:", payload, flush=True)
            print("Published state:", payload, flush=True)

        except Exception as error:
            print("MAIN ERROR:", error, flush=True)

            fallback_payload = {
                **DEFAULT_SOLIS_DATA,
                **DEFAULT_AI_DATA,
            }

            try:
                mqtt.publish("solid/state", fallback_payload, retain=True)
                print("Published fallback state:", fallback_payload, flush=True)
            except Exception as mqtt_error:
                print("MQTT fallback publish error:", mqtt_error, flush=True)

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
from mqtt import MqttClient
from solis_client import SolisClient


DEFAULT_SOLIS_DATA = {
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
}


DEFAULT_AI_DATA = {
    "advice": "Analyse IA en attente de donnees.",
    "tempo": 0,
    "tempo_label": "Inconnu",
    "tempo_tomorrow": 0,
    "tempo_tomorrow_label": "Inconnu",
    "pv_forecast_kw": 0.0,
    "prediction": "Prediction indisponible",
    "energy_mode": "Indisponible",
