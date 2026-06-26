import json
import os
from datetime import datetime, timedelta

from tempo import Tempo
from weather import Weather


class AiEngine:
    def __init__(self):
        self.tempo = Tempo()
        self.weather = Weather()
        self.history_file = os.getenv("HISTORY_FILE", "/data/solid_ems_history.json")
        self.battery_capacity_kwh = float(os.getenv("BATTERY_CAPACITY_KWH", "30"))
        self.history_days = int(os.getenv("HISTORY_DAYS", "14"))

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
            "pv1_power": self._to_float(data.get("pv1_power")),
            "pv2_power": self._to_float(data.get("pv2_power")),
            "pv_total_dc_power": self._to_float(data.get("pv_total_dc_power")),
            "load_power": self._to_float(data.get("load_power")),
            "battery_soc": self._to_float(data.get("battery_soc")),
            "battery_power": self._to_float(data.get("battery_power")),
            "grid_power": self._to_float(data.get("grid_power")),
        }
        history.append(sample)
        self._save_history(history)

    def _average_for_hour(self, key, target_hour, min_value=0.0):
        history = self._load_history()
        values = [self._to_float(item.get(key)) for item in history if item.get("hour") == target_hour]
        values = [value for value in values if value > min_value]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _average_load_for_hour(self, target_hour):
        return self._average_for_hour("load_power", target_hour, 0.0)

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

    def _average_string_for_hour(self, string_key, target_hour):
        return self._average_for_hour(string_key, target_hour, 0.2)

    def _analyze_pv_strings(self, pv1_power, pv2_power, pv_total_dc_power, pv_power):
        pv1 = self._to_float(pv1_power)
        pv2 = self._to_float(pv2_power)
        pv_dc = self._to_float(pv_total_dc_power)
        pv_ac = self._to_float(pv_power)
        now_hour = datetime.now().hour
        status = "OK"
        alert = "Strings PV conformes a leur comportement habituel"
        max_deviation_pct = 0.0
        priority = 0

        if pv_dc < 0.8 and pv_ac < 0.8:
            return {
                "pv_string_status": "LOW_LIGHT",
                "pv_string_alert": "Production trop faible pour diagnostiquer les strings",
                "pv_string_imbalance_pct": 0.0,
                "pv_string_priority": 0,
            }

        pv1_reference = self._average_string_for_hour("pv1_power", now_hour)
        pv2_reference = self._average_string_for_hour("pv2_power", now_hour)

        if pv1_reference <= 0 or pv2_reference <= 0:
            return {
                "pv_string_status": "LEARNING",
                "pv_string_alert": "Apprentissage en cours : historique strings PV insuffisant",
                "pv_string_imbalance_pct": 0.0,
                "pv_string_priority": 0,
            }

        pv1_ratio = pv1 / pv1_reference if pv1_reference > 0 else 1
        pv2_ratio = pv2 / pv2_reference if pv2_reference > 0 else 1
        pv1_drop_pct = max(0, (1 - pv1_ratio) * 100)
        pv2_drop_pct = max(0, (1 - pv2_ratio) * 100)
        max_deviation_pct = max(pv1_drop_pct, pv2_drop_pct)

        if pv1_reference > 1.0 and pv1 < 0.15:
            status = "CRITICAL"
            alert = "Possible defaut String PV 1 : production quasi nulle par rapport a son historique"
            priority = 6
        elif pv2_reference > 1.0 and pv2 < 0.15:
            status = "CRITICAL"
            alert = "Possible defaut String PV 2 : production quasi nulle par rapport a son historique"
            priority = 6
        elif pv1_drop_pct >= 45 and pv1_reference > 0.8:
            status = "WARNING"
            alert = "String PV 1 nettement sous son niveau habituel : verifier ombrage, connectique ou panneau"
            priority = 5
        elif pv2_drop_pct >= 45 and pv2_reference > 0.8:
            status = "WARNING"
            alert = "String PV 2 nettement sous son niveau habituel : verifier ombrage, connectique ou panneau"
            priority = 5
        elif pv1_drop_pct >= 30 and pv1_reference > 0.8:
            status = "WATCH"
            alert = "String PV 1 sous son niveau habituel : tendance a surveiller"
            priority = 3
        elif pv2_drop_pct >= 30 and pv2_reference > 0.8:
            status = "WATCH"
            alert = "String PV 2 sous son niveau habituel : tendance a surveiller"
            priority = 3

        if pv_dc > 1.0 and pv_ac > 0:
            ac_dc_ratio = pv_ac / pv_dc
            if ac_dc_ratio < 0.65:
                status = "WARNING"
                alert = "Ecart important entre puissance DC panneaux et puissance AC onduleur"
                priority = max(priority, 4)
                max_deviation_pct = max(max_deviation_pct, round((1 - ac_dc_ratio) * 100, 1))

        return {
            "pv_string_status": status,
            "pv_string_alert": alert,
            "pv_string_imbalance_pct": self._safe_round(max_deviation_pct, 1),
            "pv_string_priority": priority,
        }

    def _estimate_pv_forecast(self, current_pv):
        try:
            weather = self.weather.get_forecast()
        except Exception as error:
            print("AI weather error:", error, flush=True)
            weather = {}
        radiation = self._to_float(weather.get("radiation"))
        cloud = self._to_float(weather.get("cloud"), 100)
        pv_forecast = radiation * (1 - cloud / 100)
        pv_estimated_kw = pv_forecast / 200
        if current_pv > pv_estimated_kw:
            pv_estimated_kw = current_pv
        return self._safe_round(max(0, pv_estimated_kw), 1)

    def _estimate_autonomy_hours(self, battery_soc, load_power):
        if battery_soc <= 0 or load_power <= 0:
            return 0.0
        available_kwh = self.battery_capacity_kwh * battery_soc / 100
        return self._safe_round(available_kwh / load_power, 1)

    def _estimate_full_charge_hours(self, battery_soc, battery_power, pv_power, load_power):
        if battery_soc >= 100:
            return 0.0
        remaining_kwh = self.battery_capacity_kwh * (100 - battery_soc) / 100
        charge_power = max(self._to_float(battery_power), self._to_float(pv_power) - self._to_float(load_power), 0)
        if charge_power <= 0:
            return 0.0
        return self._safe_round(remaining_kwh / charge_power, 1)

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

    def _build_advice(self, tempo_today, tempo_tomorrow, battery_soc, pv_power, load_power, grid_power,
                      pv_forecast_kw, habit_load_next_6h, estimated_autonomy_h, estimated_full_h,
                      pv_string_analysis):
        advice = []
        priority = 0
        pv_string_priority = pv_string_analysis.get("pv_string_priority", 0)
        pv_string_status = pv_string_analysis.get("pv_string_status", "OK")
        pv_string_alert = pv_string_analysis.get("pv_string_alert", "")

        if pv_string_status in ["CRITICAL", "WARNING"]:
            advice.append(pv_string_alert)
            priority = max(priority, pv_string_priority)

        if tempo_tomorrow == 3:
            advice.append("Demain sera rouge : charger au maximum la batterie aujourd'hui et decaler les usages importants.")
            priority = max(priority, 6)
            if battery_soc < 85:
                advice.append("Objectif recommande : viser au moins 85 % de batterie avant demain matin.")
                priority = max(priority, 6)
        elif tempo_tomorrow == 2:
            advice.append("Demain sera blanc : conserver une marge batterie et eviter les usages lourds demain en heures pleines.")
            priority = max(priority, 3)

        if tempo_today == 3:
            advice.append("Aujourd'hui est rouge : limiter les gros consommateurs et privilegier la batterie.")
            priority = max(priority, 6)
            if grid_power > 0.1:
                advice.append("Import reseau detecte en jour rouge : reduire immediatement les charges non critiques.")
                priority = max(priority, 7)
        elif tempo_today == 2:
            advice.append("Tempo blanc aujourd'hui : eviter les usages lourds en heures pleines si possible.")
            priority = max(priority, 3)
        elif tempo_today == 1:
            if pv_power > load_power and battery_soc > 60:
                advice.append("Tempo bleu et surplus solaire : bon moment pour lancer les appareils energivores.")
                priority = max(priority, 3)
            else:
                advice.append("Tempo bleu : jour favorable, surveiller le surplus solaire et la batterie.")
                priority = max(priority, 2)

        if battery_soc < 20:
            advice.append("Batterie faible : limiter la consommation jusqu'au retour d'une production suffisante.")
            priority = max(priority, 6)
        elif battery_soc < 35 and tempo_tomorrow == 3:
            advice.append("Batterie trop basse avant un jour rouge : eviter toute decharge inutile.")
            priority = max(priority, 6)

        if pv_power > load_power and battery_soc < 95:
            advice.append("Production PV superieure a la maison : laisser charger la batterie.")
            priority = max(priority, 3)
        if pv_power > load_power and battery_soc >= 95:
            advice.append("Batterie presque pleine et surplus solaire : lancer les usages flexibles maintenant.")
            priority = max(priority, 4)
        if habit_load_next_6h > load_power * 1.25 and battery_soc < 50:
            advice.append("La consommation habituelle des prochaines heures est elevee : conserver la batterie.")
            priority = max(priority, 4)
        if pv_forecast_kw < 1 and battery_soc < 50:
            advice.append("Faible production solaire prevue : garder une reserve batterie.")
            priority = max(priority, 4)
        if estimated_autonomy_h > 0 and estimated_autonomy_h < 3:
            advice.append(f"Autonomie batterie estimee faible : environ {estimated_autonomy_h} h au rythme actuel.")
            priority = max(priority, 4)
        if estimated_full_h > 0 and estimated_full_h <= 3:
            advice.append(f"Batterie probablement pleine dans environ {estimated_full_h} h.")
            priority = max(priority, 2)
        if not advice:
            advice.append("Systeme optimal : aucune action particuliere recommandee.")
            priority = max(priority, 1)
        return advice[0], priority

    def analyze(self, data):
        try:
            self._record_sample(data)
            pv_power = self._to_float(data.get("pv_power"))
            pv1_power = self._to_float(data.get("pv1_power"))
            pv2_power = self._to_float(data.get("pv2_power"))
            pv_total_dc_power = self._to_float(data.get("pv_total_dc_power"))
            load_power = self._to_float(data.get("load_power"))
            battery_soc = self._to_float(data.get("battery_soc"))
            battery_power = self._to_float(data.get("battery_power"))
            grid_power = self._to_float(data.get("grid_power"))

            tempo_data = self.tempo.get_tempo_data()
            tempo_today = int(tempo_data.get("tempo", 0))
            tempo_label = tempo_data.get("tempo_label", "Inconnu")
            tempo_tomorrow = int(tempo_data.get("tempo_tomorrow", 0))
            tempo_tomorrow_label = tempo_data.get("tempo_tomorrow_label", "Inconnu")

            pv_forecast_kw = self._estimate_pv_forecast(pv_power)
            habit_load_now = self._average_load_for_hour(datetime.now().hour)
            habit_load_next_6h = self._average_load_next_hours(6)
            estimated_autonomy_h = self._estimate_autonomy_hours(battery_soc, max(load_power, habit_load_now))
            estimated_full_h = self._estimate_full_charge_hours(battery_soc, battery_power, pv_power, load_power)
            energy_mode = self._detect_energy_mode(pv_power, load_power, battery_power, grid_power)
            pv_string_analysis = self._analyze_pv_strings(pv1_power, pv2_power, pv_total_dc_power, pv_power)

            advice, priority = self._build_advice(
                tempo_today, tempo_tomorrow, battery_soc, pv_power, load_power, grid_power,
                pv_forecast_kw, habit_load_next_6h, estimated_autonomy_h, estimated_full_h,
                pv_string_analysis,
            )

            if priority >= 5:
                confidence = "high"
            elif priority >= 3:
                confidence = "medium"
            else:
                confidence = "normal"

            prediction = f"{energy_mode}. PV prevu: {pv_forecast_kw} kW. Autonomie estimee: {estimated_autonomy_h} h."

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
                "pv_string_status": pv_string_analysis.get("pv_string_status"),
                "pv_string_alert": pv_string_analysis.get("pv_string_alert"),
                "pv_string_imbalance_pct": pv_string_analysis.get("pv_string_imbalance_pct"),
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
                "pv_string_status": "UNKNOWN",
                "pv_string_alert": "Diagnostic strings PV indisponible",
                "pv_string_imbalance_pct": 0,
            }
