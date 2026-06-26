import json
import os
import time
from datetime import datetime, timedelta

from tempo import Tempo
from weather import Weather


class AiEngine:
    def __init__(self):
        self.tempo = Tempo()
        self.weather = Weather()

        self.history_file = os.getenv(
            "HISTORY_FILE",
            "/data/solid_ems_history.json",
        )

        self.battery_capacity_kwh = float(
            os.getenv("BATTERY_CAPACITY_KWH", "30")
        )

        self.history_days = int(os.getenv("HISTORY_DAYS", "14"))

    # -------------------------
    # SAFE HELPERS
    # -------------------------
    def _to_float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_round(self, value, digits=2):
        try:
            return round(float(value), digits)
        except (TypeError, ValueError):
            return 0.0

    # -------------------------
    # HISTORY STORAGE
    # -------------------------
    def _load_history(self):
        try:
            if not os.path.exists(self.history_file):
                return []

            with open(self.history_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            return data

        except Exception as error:
            print("AI history load error:", error, flush=True)
            return []

    def _save_history(self, history):
        try:
            directory = os.path.dirname(self.history_file)
            os.makedirs(directory, exist_ok=True)

            cutoff = datetime.now() - timedelta(days=self.history_days)

            cleaned = []
            for item in history:
                try:
                    ts = datetime.fromisoformat(item["timestamp"])
                    if ts >= cutoff:
                        cleaned.append(item)
                except Exception:
                    continue

            with open(self.history_file, "w", encoding="utf-8") as file:
                json.dump(cleaned, file)

        except Exception as error:
            print("AI history save error:", error, flush=True)

    def _record_sample(self, data):
        history = self._load_history()

        now = datetime.now()

        sample = {
            "timestamp": now.isoformat(timespec="seconds"),
            "hour": now.hour,
            "weekday": now.weekday(),
            "pv_power": self._to_float(data.get("pv_power")),
            "load_power": self._to_float(data.get("load_power")),
            "battery_soc": self._to_float(data.get("battery_soc")),
            "battery_power": self._to_float(data.get("battery_power")),
            "grid_power": self._to_float(data.get("grid_power")),
        }

        history.append(sample)
        self._save_history(history)

    # -------------------------
    # HABIT LEARNING
    # -------------------------
    def _average_load_for_hour(self, target_hour):
        history = self._load_history()

        values = [
            self._to_float(item.get("load_power"))
            for item in history
            if item.get("hour") == target_hour
        ]

        values = [value for value in values if value > 0]

        if not values:
            return 0.0

        return sum(values) / len(values)

    def _average_load_next_hours(self, hours=6):
        now = datetime.now()
        values = []

        for index in range(hours):
            target_hour = (now.hour + index) % 24
            value = self._average_load_for_hour(target_hour)
            if value > 0:
                values.append(value)

        if not values:
            return 0.0

        return sum(values) / len(values)

    # -------------------------
    # TEMPO TEXT
    # -------------------------
    def _tempo_text(self, code, label):
        if code == 1:
            return "Bleu"
        if code == 2:
            return "Blanc"
        if code == 3:
            return "Rouge"
        return label or "Inconnu"

    # -------------------------
    # WEATHER / PV FORECAST
    # -------------------------
    def _estimate_pv_forecast(self, current_pv):
        try:
            weather = self.weather.get_forecast()
        except Exception as error:
            print("AI weather error:", error, flush=True)
            weather = {}

        radiation = self._to_float(weather.get("radiation"))
        cloud = self._to_float(weather.get("cloud"), 100)

        pv_forecast = radiation * (1 - cloud / 100)

        # Simple scaling factor.
        # This is intentionally conservative.
        pv_estimated_kw = pv_forecast / 200

        # If current production is already higher, keep current trend.
        if current_pv > pv_estimated_kw:
            pv_estimated_kw = current_pv

        return self._safe_round(max(0, pv_estimated_kw), 1)

    # -------------------------
    # BATTERY ESTIMATIONS
    # -------------------------
    def _estimate_autonomy_hours(self, battery_soc, load_power):
        if battery_soc <= 0 or load_power <= 0:
            return 0.0

        available_kwh = self.battery_capacity_kwh * battery_soc / 100
        autonomy = available_kwh / load_power

        return self._safe_round(autonomy, 1)

    def _estimate_full_charge_hours(self, battery_soc, battery_power, pv_power, load_power):
        if battery_soc >= 100:
            return 0.0

        remaining_kwh = self.battery_capacity_kwh * (100 - battery_soc) / 100

        # Solis battery_power positive is considered charge power in our current mapping.
        charge_power = max(
            self._to_float(battery_power),
            self._to_float(pv_power) - self._to_float(load_power),
            0,
        )

        if charge_power <= 0:
            return 0.0

        hours = remaining_kwh / charge_power

        return self._safe_round(hours, 1)

    # -------------------------
    # MODE DETECTION
    # -------------------------
    def _detect_energy_mode(self, pv_power, load_power, battery_power, grid_power):
        if pv_power <= 0.1 and load_power > 0:
            return "Nuit / faible production"

        if pv_power > load_power and battery_power > 0:
            return "PV alimente maison et charge batterie"

        if grid_power < -0.1:
            return "Injection reseau"

        if grid_power > 0.1:
            return "Import reseau"

        if battery_power < -0.1:
            return "Batterie en decharge"

        return "Autoconsommation stable"

    # -------------------------
    # ADVICE ENGINE
    # -------------------------
    def _build_advice(
        self,
        tempo_today,
        tempo_tomorrow,
        battery_soc,
        pv_power,
        load_power,
        grid_power,
        pv_forecast_kw,
        habit_load_next_6h,
        estimated_autonomy_h,
        estimated_full_h,
    ):
        advice = []
        priority = 0

        # Tomorrow red has very high priority.
        if tempo_tomorrow == 3:
            advice.append(
                "Demain sera rouge : charger au maximum la batterie aujourd'hui et decaler les usages importants."
            )
            priority = max(priority, 5)

            if battery_soc < 85:
                advice.append(
                    "Objectif recommande : viser au moins 85 % de batterie avant demain matin."
                )
                priority = max(priority, 5)

        # Today red.
        if tempo_today == 3:
            advice.append(
                "Aujourd'hui est rouge : limiter les gros consommateurs et privilegier la batterie."
            )
            priority = max(priority, 5)

            if grid_power > 0.1:
                advice.append(
                    "Import reseau detecte en jour rouge : reduire immediatement les charges non critiques."
                )
                priority = max(priority, 6)

        # White day.
        if tempo_today == 2:
            advice.append(
                "Tempo blanc : eviter les usages lourds en heures pleines si possible."
            )
            priority = max(priority, 3)

        # Blue day.
        if tempo_today == 1 and tempo_tomorrow != 3:
            if pv_power > load_power and battery_soc > 60:
                advice.append(
                    "Tempo bleu et surplus solaire : bon moment pour lancer les appareils energivores."
                )
                priority = max(priority, 3)
            else:
                advice.append(
                    "Tempo bleu : jour favorable, mais surveiller la batterie et le surplus solaire."
                )
                priority = max(priority, 2)

        # Battery protection.
        if battery_soc < 20:
            advice.append(
                "Batterie faible : limiter la consommation jusqu'au retour d'une production suffisante."
            )
            priority = max(priority, 5)

        elif battery_soc < 35 and tempo_tomorrow == 3:
            advice.append(
                "Batterie trop basse avant un jour rouge : eviter toute decharge inutile."
            )
            priority = max(priority, 5)

        # PV situation.
        if pv_power > load_power and battery_soc < 95:
            advice.append(
                "Production PV superieure a la maison : laisser charger la batterie."
            )
            priority = max(priority, 3)

        if pv_power > load_power and battery_soc >= 95:
            advice.append(
                "Batterie presque pleine et surplus solaire : lancer les usages flexibles maintenant."
            )
            priority = max(priority, 4)

        # Habits.
        if habit_load_next_6h > load_power * 1.25 and battery_soc < 50:
            advice.append(
                "La consommation habituelle des prochaines heures est elevee : conserver la batterie."
            )
            priority = max(priority, 4)

        # Forecast.
        if pv_forecast_kw < 1 and battery_soc < 50:
            advice.append(
                "Faible production solaire prevue : garder une reserve batterie."
            )
            priority = max(priority, 4)

        if estimated_autonomy_h > 0 and estimated_autonomy_h < 3:
            advice.append(
                f"Autonomie batterie estimee faible : environ {estimated_autonomy_h} h au rythme actuel."
            )
            priority = max(priority, 4)

        if estimated_full_h > 0 and estimated_full_h <= 3:
            advice.append(
                f"Batterie probablement pleine dans environ {estimated_full_h} h."
            )
            priority = max(priority, 2)

        if not advice:
            advice.append("Systeme optimal : aucune action particuliere recommandee.")
            priority = max(priority, 1)

        return advice[0], priority

    # -------------------------
    # MAIN ANALYSIS
    # -------------------------
    def analyze(self, data):
        try:
            self._record_sample(data)

            pv_power = self._to_float(data.get("pv_power"))
            load_power = self._to_float(data.get("load_power"))
            battery_soc = self._to_float(data.get("battery_soc"))
            battery_power = self._to_float(data.get("battery_power"))
            grid_power = self._to_float(data.get("grid_power"))

            tempo_data = self.tempo.get_tempo_data()

            tempo_today = int(tempo_data.get("tempo", 0))
            tempo_label = self._tempo_text(
                tempo_today,
                tempo_data.get("tempo_label", "Inconnu"),
            )

            tempo_tomorrow = int(tempo_data.get("tempo_tomorrow", 0))
            tempo_tomorrow_label = self._tempo_text(
                tempo_tomorrow,
                tempo_data.get("tempo_tomorrow_label", "Inconnu"),
            )

            pv_forecast_kw = self._estimate_pv_forecast(pv_power)

            habit_load_now = self._average_load_for_hour(datetime.now().hour)
            habit_load_next_6h = self._average_load_next_hours(6)

            estimated_autonomy_h = self._estimate_autonomy_hours(
                battery_soc,
                max(load_power, habit_load_now),
            )

            estimated_full_h = self._estimate_full_charge_hours(
                battery_soc,
                battery_power,
                pv_power,
                load_power,
            )

            energy_mode = self._detect_energy_mode(
                pv_power,
                load_power,
                battery_power,
                grid_power,
            )

            advice, priority = self._build_advice(
                tempo_today=tempo_today,
                tempo_tomorrow=tempo_tomorrow,
                battery_soc=battery_soc,
                pv_power=pv_power,
                load_power=load_power,
                grid_power=grid_power,
                pv_forecast_kw=pv_forecast_kw,
                habit_load_next_6h=habit_load_next_6h,
                estimated_autonomy_h=estimated_autonomy_h,
                estimated_full_h=estimated_full_h,
            )

            if priority >= 5:
                confidence = "high"
            elif priority >= 3:
                confidence = "medium"
            else:
                confidence = "normal"

            prediction = (
                f"{energy_mode}. PV prevu: {pv_forecast_kw} kW. "
                f"Autonomie estimee: {estimated_autonomy_h} h."
            )

            if estimated_full_h > 0:
                battery_strategy = f"Charge complete estimee dans {estimated_full_h} h"
            elif battery_soc >= 95:
                battery_strategy = "Batterie presque pleine"
            elif battery_soc < 25:
                battery_strategy = "Preserver la batterie"
            else:
                battery_strategy = "Gestion batterie normale"

            return {
                "advice": advice,
                "tempo": tempo_today,
                "tempo_label": tempo_label,
                "tempo_tomorrow": tempo_tomorrow,
                "tempo_tomorrow_label": tempo_tomorrow_label,
                "pv_forecast_kw": pv_forecast_kw,
                "prediction": prediction,
                "energy_mode": energy_mode,
                "battery_strategy": battery_strategy,
                "estimated_autonomy_h": estimated_autonomy_h,
                "estimated_battery_full_h": estimated_full_h,
                "habit_load_now_kw": self._safe_round(habit_load_now, 2),
                "habit_load_next_6h_kw": self._safe_round(habit_load_next_6h, 2),
                "advice_priority": priority,
                "advice_confidence": confidence,
            }

        except Exception as error:
            print("AI engine error:", error, flush=True)

            return {
                "advice": "Analyse IA indisponible temporairement.",
                "tempo": 0,
                "tempo_label": "Inconnu",
                "tempo_tomorrow": 0,
                "tempo_tomorrow_label": "Inconnu",
                "pv_forecast_kw": 0,
                "prediction": "Prediction indisponible",
                "energy_mode": "Indisponible",
                "battery_strategy": "Indisponible",
                "estimated_autonomy_h": 0,
                "estimated_battery_full_h": 0,
                "habit_load_now_kw": 0,
                "habit_load_next_6h_kw": 0,
                "advice_priority": 0,
                "advice_confidence": "low",
            }
