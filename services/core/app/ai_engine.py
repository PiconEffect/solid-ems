import json
import math
import os
from datetime import datetime, timedelta

from tempo import Tempo
from weather import Weather


# -----------------------------------------------------------------------------
# Fixed PV installation model for this SOLID EMS installation.
# Convention azimuth_deg:
#   0   = south
#   +35 = south-south-west / west of south
#   -35 = south-south-east / east of south
# -----------------------------------------------------------------------------
PV_SITE = {
    "latitude": 50.28,
    "longitude": 2.80,
}

PV_ARRAYS = {
    "pv1": {
        "label": "PV1 sud-sud-ouest",
        "kwp": 5.15,
        "panels": 10,
        "panel_wp": 515,
        "azimuth_deg": 35.0,
        "tilt_deg": 30.0,
    },
    "pv2": {
        "label": "PV2 sud",
        "kwp": 4.41,
        "panels": 9,
        "panel_wp": 490,
        "azimuth_deg": 0.0,
        "tilt_deg": 30.0,
    },
}

PV_TOTAL_KWP = PV_ARRAYS["pv1"]["kwp"] + PV_ARRAYS["pv2"]["kwp"]
PV_TEMP_COEFF_PCT_PER_C = -0.40
PV_REF_TEMP_C = 25.0
PV_MODEL_DERATE = 0.88

# Inverter / grid / battery power limits used by the embedded AI.
# These limits are intentionally kept in ai_engine.py because they describe this fixed installation.
# If the installation contract/settings change, update these constants only.
# Fixed installation: Solis S6-EH1P6K-L-PLUS.
# Datasheet model 6K:
# - max recommended PV array size: 12 kW
# - max usable PV input power: 9.6 kW
# - nominal AC output power: 6 kW
# - max battery charge/discharge power: 6 kW
# - max AC input current: 40 A, approximated as 9.2 kW at 230 V
INVERTER_AC_POWER_LIMIT_KW = 6.0
PV_DC_INSTALLED_LIMIT_KW = PV_TOTAL_KWP
PV_DC_RECOMMENDED_MAX_KW = 12.0
PV_DC_USABLE_LIMIT_KW = 9.6
BATTERY_CHARGE_LIMIT_KW = 6.0
BATTERY_DISCHARGE_LIMIT_KW = 6.0
GRID_EXPORT_LIMIT_KW = 0.0
GRID_IMPORT_LIMIT_KW = 9.2
LIMIT_MARGIN_KW = 0.35


class AiEngine:
    def __init__(self):
        self.tempo = Tempo()
        self.weather = Weather()
        self.history_file = os.getenv("HISTORY_FILE", "/data/solid_ems_history.json")
        self.battery_capacity_kwh = float(os.getenv("BATTERY_CAPACITY_KWH", "30"))
        self.history_days = int(os.getenv("HISTORY_DAYS", "14"))

        # AI thresholds. Kept internal to avoid touching .env / HA / discovery.
        self.flexible_load_min_surplus_kw = 1.5
        self.flexible_load_min_duration_h = 2
        self.red_day_target_soc = 90.0
        self.white_day_target_soc = 70.0
        self.low_soc_threshold = 25.0
        self.high_soc_threshold = 85.0
        self.pv_expected_min_kw_for_alarm = 1.0
        self.pv_perf_warning_pct = 65.0
        self.pv_perf_watch_pct = 78.0

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

    def _limit_text(self, value, max_len=240):
        """
        Home Assistant sensor states must stay short. If a text state is too long,
        HA can mark the entity as unknown/unavailable. Keep advice/prediction compact.
        """
        if value is None:
            return ""
        text = str(value).replace("\n", " ").strip()
        while "  " in text:
            text = text.replace("  ", " ")
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rstrip() + "…"

    def _clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

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
                json.dump(cleaned, file, ensure_ascii=False)
        except Exception as error:
            print("AI history save error:", error, flush=True)

    def _record_sample(self, data):
        history = self._load_history()
        now = datetime.now()
        sample = {
            "timestamp": now.isoformat(timespec="seconds"),
            "hour": now.hour,
            "weekday": now.weekday(),
            "day_of_year": now.timetuple().tm_yday,
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

    def _history_values_for_hour(self, key, target_hour, min_value=0.0):
        history = self._load_history()
        values = [
            self._to_float(item.get(key))
            for item in history
            if item.get("hour") == target_hour
        ]
        return [value for value in values if value > min_value]

    def _average_for_hour(self, key, target_hour, min_value=0.0):
        values = self._history_values_for_hour(key, target_hour, min_value)
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _average_load_for_hour(self, target_hour):
        return self._average_for_hour("load_power", target_hour, 0.0)

    def _average_pv_for_hour(self, target_hour):
        return self._average_for_hour("pv_power", target_hour, 0.0)

    def _average_string_for_hour(self, string_key, target_hour):
        return self._average_for_hour(string_key, target_hour, 0.2)

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

    def _average_energy_next_hours(self, key, hours=6):
        now = datetime.now()
        total = 0.0
        count = 0
        for index in range(hours):
            target_hour = (now.hour + index) % 24
            if key == "load_power":
                value = self._average_load_for_hour(target_hour)
            else:
                value = self._average_pv_for_hour(target_hour)
            if value > 0:
                total += value
                count += 1
        return total if count else 0.0

    # -------------------------------------------------------------------------
    # Weather and local solar model
    # -------------------------------------------------------------------------
    def _get_weather_context(self):
        try:
            weather = self.weather.get_forecast()
            if not isinstance(weather, dict):
                weather = {}
        except Exception as error:
            print("AI weather error:", error, flush=True)
            weather = {}

        radiation = self._to_float(weather.get("radiation"), 0.0)
        cloud = self._to_float(weather.get("cloud"), 100.0)
        temperature = self._to_float(weather.get("temperature"), 0.0)
        rain = self._to_float(weather.get("rain"), 0.0)

        cloud_factor = self._clamp(1.0 - cloud / 100.0, 0.05, 1.0)
        radiation_factor = self._clamp(radiation / 800.0, 0.05, 1.25) if radiation > 0 else cloud_factor
        weather_factor = self._clamp((cloud_factor * 0.55) + (radiation_factor * 0.45), 0.05, 1.20)

        if cloud <= 25 and radiation >= 450:
            label = "beau temps"
        elif cloud <= 55 and radiation >= 250:
            label = "production correcte"
        elif cloud >= 80 or radiation < 120:
            label = "faible production probable"
        else:
            label = "production incertaine"

        return {
            "raw": weather,
            "radiation": radiation,
            "cloud": cloud,
            "temperature": temperature,
            "rain": rain,
            "factor": weather_factor,
            "label": label,
        }

    def _timezone_offset_hours(self, now):
        try:
            offset = now.astimezone().utcoffset()
            if offset is None:
                return 1.0
            return offset.total_seconds() / 3600.0
        except Exception:
            return 1.0

    def _solar_position(self, now=None):
        now = now or datetime.now()
        lat = math.radians(PV_SITE["latitude"])
        day = now.timetuple().tm_yday
        hour_decimal = now.hour + now.minute / 60.0 + now.second / 3600.0

        # Approximate solar declination and equation of time.
        gamma = 2.0 * math.pi * (day - 1 + (hour_decimal - 12.0) / 24.0) / 365.0
        decl = (
            0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.001480 * math.sin(3 * gamma)
        )
        eq_time_min = 229.18 * (
            0.000075
            + 0.001868 * math.cos(gamma)
            - 0.032077 * math.sin(gamma)
            - 0.014615 * math.cos(2 * gamma)
            - 0.040849 * math.sin(2 * gamma)
        )

        tz = self._timezone_offset_hours(now)
        time_offset_min = eq_time_min + 4.0 * PV_SITE["longitude"] - 60.0 * tz
        true_solar_time_h = (hour_decimal * 60.0 + time_offset_min) / 60.0
        hour_angle_deg = 15.0 * (true_solar_time_h - 12.0)
        hour_angle = math.radians(hour_angle_deg)

        sin_elev = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(hour_angle)
        sin_elev = self._clamp(sin_elev, -1.0, 1.0)
        elevation = math.asin(sin_elev)
        elevation_deg = math.degrees(elevation)

        # South-relative sun azimuth approximation: negative morning/east, positive afternoon/west.
        south_relative_azimuth_deg = hour_angle_deg
        daylight_factor = max(0.0, math.sin(elevation))

        return {
            "day_of_year": day,
            "hour_decimal": hour_decimal,
            "solar_time_h": true_solar_time_h,
            "hour_angle_deg": hour_angle_deg,
            "elevation_deg": elevation_deg,
            "south_relative_azimuth_deg": south_relative_azimuth_deg,
            "daylight_factor": daylight_factor,
        }

    def _season_factor(self, solar_position):
        # Normalized seasonal potential from solar elevation. Kept conservative because
        # cloud/radiation and local history already correct the estimate.
        elevation = solar_position.get("elevation_deg", 0.0)
        if elevation <= 0:
            return 0.0
        return self._clamp(math.sin(math.radians(elevation)) / math.sin(math.radians(62.0)), 0.05, 1.10)

    def _temperature_factor(self, temperature_c):
        if temperature_c <= 0:
            return 1.0
        delta = temperature_c - PV_REF_TEMP_C
        factor = 1.0 + (PV_TEMP_COEFF_PCT_PER_C / 100.0) * delta
        return self._clamp(factor, 0.75, 1.08)

    def _array_orientation_factor(self, array_meta, solar_position):
        elevation_deg = solar_position.get("elevation_deg", 0.0)
        if elevation_deg <= 0:
            return 0.0

        tilt_deg = array_meta["tilt_deg"]
        panel_azimuth_deg = array_meta["azimuth_deg"]
        sun_south_azimuth_deg = solar_position.get("south_relative_azimuth_deg", 0.0)

        # South-relative azimuth alignment. PV1 SSO is naturally favoured after solar noon.
        azimuth_delta = math.radians(sun_south_azimuth_deg - panel_azimuth_deg)
        azimuth_factor = max(0.0, math.cos(azimuth_delta))

        # Simple tilt factor: best when panel tilt roughly sees the current solar elevation.
        incidence_delta = abs((90.0 - elevation_deg) - tilt_deg)
        tilt_factor = self._clamp(math.cos(math.radians(incidence_delta)), 0.25, 1.0)

        elevation_factor = max(0.0, math.sin(math.radians(elevation_deg)))
        return self._clamp(elevation_factor * azimuth_factor * (0.65 + 0.35 * tilt_factor), 0.0, 1.0)

    def _expected_array_power(self, array_key, weather_context, solar_position):
        meta = PV_ARRAYS[array_key]
        orientation_factor = self._array_orientation_factor(meta, solar_position)
        season_factor = self._season_factor(solar_position)
        weather_factor = self._to_float(weather_context.get("factor"), 0.5)
        temp_factor = self._temperature_factor(self._to_float(weather_context.get("temperature"), 0.0))

        expected = meta["kwp"] * orientation_factor * season_factor * weather_factor * temp_factor * PV_MODEL_DERATE
        return self._safe_round(max(0.0, expected), 2)

    def _expected_pv_performance(self, pv1_power, pv2_power, pv_power, weather_context):
        solar_position = self._solar_position()
        pv1_expected_physics = self._expected_array_power("pv1", weather_context, solar_position)
        pv2_expected_physics = self._expected_array_power("pv2", weather_context, solar_position)

        now_hour = datetime.now().hour
        pv1_history = self._average_string_for_hour("pv1_power", now_hour)
        pv2_history = self._average_string_for_hour("pv2_power", now_hour)
        weather_factor = self._to_float(weather_context.get("factor"), 0.5)

        # Blend physics and local historical behaviour. History is useful for local shade,
        # inverter behaviour and real site specifics; physics catches seasonal/day effects.
        if pv1_history > 0:
            pv1_expected = 0.65 * pv1_expected_physics + 0.35 * (pv1_history * weather_factor)
        else:
            pv1_expected = pv1_expected_physics

        if pv2_history > 0:
            pv2_expected = 0.65 * pv2_expected_physics + 0.35 * (pv2_history * weather_factor)
        else:
            pv2_expected = pv2_expected_physics

        pv_expected = pv1_expected + pv2_expected
        actual_total = max(self._to_float(pv_power), self._to_float(pv1_power) + self._to_float(pv2_power))

        def ratio(actual, expected):
            if expected < 0.2:
                return 0.0
            return self._safe_round(actual / expected * 100.0, 1)

        return {
            "solar_position": solar_position,
            "pv1_expected_kw": self._safe_round(pv1_expected, 2),
            "pv2_expected_kw": self._safe_round(pv2_expected, 2),
            "pv_expected_kw": self._safe_round(pv_expected, 2),
            "pv1_performance_ratio_pct": ratio(pv1_power, pv1_expected),
            "pv2_performance_ratio_pct": ratio(pv2_power, pv2_expected),
            "pv_performance_ratio_pct": ratio(actual_total, pv_expected),
        }

    def _analyze_power_limits(self, pv_power, pv_total_dc_power, load_power, battery_power, grid_power, battery_soc, pv_expected_kw):
        """
        Analyse les limites physiques/réglementaires de l'installation sans mélanger :
        - limite AC onduleur 6 kW,
        - limite PV DC utilisable 9,6 kW,
        - limite de charge batterie 6 kW,
        - limite de décharge batterie 6 kW,
        - limite de réinjection réseau.

        Convention existante du projet :
        - grid_power > 0 : import réseau
        - grid_power < 0 : injection réseau
        - battery_power > 0 : charge batterie
        - battery_power < 0 : décharge batterie
        """
        pv_ac = self._to_float(pv_power)
        pv_dc = self._to_float(pv_total_dc_power)
        load = self._to_float(load_power)
        batt_p = self._to_float(battery_power)
        grid_p = self._to_float(grid_power)
        soc = self._to_float(battery_soc)
        expected = self._to_float(pv_expected_kw)

        battery_charge_now = max(0.0, batt_p)
        battery_discharge_now = max(0.0, -batt_p)

        battery_charge_headroom_kw = max(0.0, BATTERY_CHARGE_LIMIT_KW - battery_charge_now)
        if soc >= 95:
            battery_charge_headroom_kw = min(battery_charge_headroom_kw, 0.3)
        elif soc >= 90:
            battery_charge_headroom_kw = min(battery_charge_headroom_kw, 1.0)

        current_export_kw = max(0.0, -grid_p)
        export_headroom_kw = max(0.0, GRID_EXPORT_LIMIT_KW - current_export_kw)
        ac_headroom_kw = max(0.0, INVERTER_AC_POWER_LIMIT_KW - pv_ac)

        # Puissance PV théorique utilisable sans bridage :
        # charge maison + marge charge batterie + marge injection.
        usable_without_curtailment_kw = load + battery_charge_headroom_kw + export_headroom_kw

        # Limite AC : uniquement liée à la puissance AC PV/onduleur,
        # pas à la puissance de charge batterie.
        ac_clipping_risk = pv_ac >= (INVERTER_AC_POWER_LIMIT_KW - LIMIT_MARGIN_KW)

        # Limite PV DC utilisable : proche de 9,6 kW pour le modèle 6K.
        pv_dc_usable_clipping_risk = pv_dc >= (PV_DC_USABLE_LIMIT_KW - LIMIT_MARGIN_KW)

        dc_ac_gap_kw = max(0.0, pv_dc - pv_ac)
        dc_ac_clipping_suspected = (
            (ac_clipping_risk or pv_dc_usable_clipping_risk)
            and dc_ac_gap_kw >= 0.5
        )

        # Limites batterie : séparées de la limite AC.
        battery_charge_near_limit = battery_charge_now >= (BATTERY_CHARGE_LIMIT_KW - LIMIT_MARGIN_KW)
        battery_charge_above_nominal = battery_charge_now > (BATTERY_CHARGE_LIMIT_KW + 0.2)
        battery_discharge_near_limit = battery_discharge_now >= (BATTERY_DISCHARGE_LIMIT_KW - LIMIT_MARGIN_KW)
        battery_discharge_above_nominal = battery_discharge_now > (BATTERY_DISCHARGE_LIMIT_KW + 0.2)

        battery_charge_limited = battery_charge_near_limit or battery_charge_above_nominal or soc >= 95
        battery_discharge_limited = battery_discharge_near_limit or battery_discharge_above_nominal

        export_limited = (
            GRID_EXPORT_LIMIT_KW <= 0.1
            or current_export_kw >= max(0.0, GRID_EXPORT_LIMIT_KW - LIMIT_MARGIN_KW)
        )

        curtailment_risk = expected > (usable_without_curtailment_kw + LIMIT_MARGIN_KW)
        effective_flexible_load_kw = max(0.0, expected - usable_without_curtailment_kw)

        messages = []

        if dc_ac_clipping_suspected:
            messages.append("Onduleur ou entrée PV proche de sa limite : un écrêtage/bridage PV est possible.")
        elif ac_clipping_risk:
            messages.append("Puissance AC PV proche de la limite 6 kW de l'onduleur.")
        elif pv_dc_usable_clipping_risk:
            messages.append("Puissance DC proche de la limite PV utilisable 9,6 kW de l'onduleur.")

        if battery_charge_above_nominal:
            messages.append("Charge batterie au-dessus de la limite théorique 6 kW : mesure probablement côté DC ou transitoire, à surveiller.")
        elif battery_charge_near_limit:
            messages.append("Charge batterie proche de la limite 6 kW : le surplus PV est presque entièrement absorbé par la batterie.")
        elif battery_discharge_above_nominal:
            messages.append("Décharge batterie au-dessus de la limite théorique 6 kW : vérifier les pics de consommation.")
        elif battery_discharge_near_limit:
            messages.append("Décharge batterie proche de la limite 6 kW : surveiller les gros consommateurs.")

        if export_limited and pv_ac > load and battery_charge_limited:
            messages.append("Réinjection réseau limitée : risque de bridage si aucun usage local n'est lancé.")
        elif export_limited and curtailment_risk:
            messages.append("Réinjection réseau limitée : surplus solaire prévu supérieur à la capacité d'absorption maison + batterie.")

        return {
            "ac_headroom_kw": self._safe_round(ac_headroom_kw, 2),
            "battery_charge_headroom_kw": self._safe_round(battery_charge_headroom_kw, 2),
            "export_headroom_kw": self._safe_round(export_headroom_kw, 2),
            "usable_without_curtailment_kw": self._safe_round(usable_without_curtailment_kw, 2),
            "effective_flexible_load_kw": self._safe_round(effective_flexible_load_kw, 2),
            "battery_charge_now_kw": self._safe_round(battery_charge_now, 2),
            "battery_discharge_now_kw": self._safe_round(battery_discharge_now, 2),
            "ac_clipping_risk": ac_clipping_risk,
            "pv_dc_usable_clipping_risk": pv_dc_usable_clipping_risk,
            "dc_ac_clipping_suspected": dc_ac_clipping_suspected,
            "battery_charge_near_limit": battery_charge_near_limit,
            "battery_charge_above_nominal": battery_charge_above_nominal,
            "battery_discharge_near_limit": battery_discharge_near_limit,
            "battery_discharge_above_nominal": battery_discharge_above_nominal,
            "battery_charge_limited": battery_charge_limited,
            "battery_discharge_limited": battery_discharge_limited,
            "export_limited": export_limited,
            "curtailment_risk": curtailment_risk,
            "messages": messages,
        }


    # -------------------------------------------------------------------------
    # PV diagnostics and energy advice
    # -------------------------------------------------------------------------
    def _analyze_pv_strings(self, pv1_power, pv2_power, pv_total_dc_power, pv_power, weather_context=None):
        weather_context = weather_context or self._get_weather_context()
        pv1 = self._to_float(pv1_power)
        pv2 = self._to_float(pv2_power)
        pv_dc = self._to_float(pv_total_dc_power)
        pv_ac = self._to_float(pv_power)
        now_hour = datetime.now().hour
        status = "OK"
        alert = "Production PV conforme au modele attendu"
        max_deviation_pct = 0.0
        priority = 0

        perf = self._expected_pv_performance(pv1, pv2, max(pv_ac, pv_dc), weather_context)
        expected_total = perf.get("pv_expected_kw", 0.0)
        perf_ratio = perf.get("pv_performance_ratio_pct", 0.0)
        pv1_ratio = perf.get("pv1_performance_ratio_pct", 0.0)
        pv2_ratio = perf.get("pv2_performance_ratio_pct", 0.0)
        solar = perf.get("solar_position", {})
        elevation = solar.get("elevation_deg", 0.0)
        sun_az = solar.get("south_relative_azimuth_deg", 0.0)

        instantaneous_den = pv1 + pv2
        if instantaneous_den > 0:
            instantaneous_imbalance = abs(pv1 - pv2) / instantaneous_den * 100
            max_deviation_pct = max(max_deviation_pct, instantaneous_imbalance)

        if pv_dc < 0.8 and pv_ac < 0.8 and expected_total < 1.0:
            return {
                "pv_string_status": "LOW_LIGHT",
                "pv_string_alert": "Production trop faible pour diagnostiquer les strings",
                "pv_string_imbalance_pct": self._safe_round(max_deviation_pct, 1),
                "pv_string_priority": 0,
                "pv_expected_kw": self._safe_round(expected_total, 2),
                "pv_performance_ratio_pct": self._safe_round(perf_ratio, 1),
                "pv1_expected_kw": perf.get("pv1_expected_kw", 0.0),
                "pv2_expected_kw": perf.get("pv2_expected_kw", 0.0),
            }

        # Performance against local physics + weather + season model.
        if expected_total >= self.pv_expected_min_kw_for_alarm:
            if perf_ratio > 0 and perf_ratio < self.pv_perf_warning_pct:
                status = "WARNING"
                alert = (
                    f"Production PV sous l'attendu : {perf_ratio} % du modele "
                    f"({self._safe_round(max(pv_ac, pv_dc), 2)} kW reels vs {expected_total} kW attendus). "
                    f"Verifier meteo locale, ombrage, encrassement ou limitation onduleur."
                )
                priority = max(priority, 5)
            elif perf_ratio > 0 and perf_ratio < self.pv_perf_watch_pct:
                status = "WATCH"
                alert = (
                    f"Production PV legerement sous l'attendu : {perf_ratio} % du modele "
                    f"({self._safe_round(max(pv_ac, pv_dc), 2)} kW reels vs {expected_total} kW attendus)."
                )
                priority = max(priority, 3)

        pv1_reference = self._average_string_for_hour("pv1_power", now_hour)
        pv2_reference = self._average_string_for_hour("pv2_power", now_hour)

        if pv1_reference > 0 and pv2_reference > 0:
            pv1_hist_ratio = pv1 / pv1_reference if pv1_reference > 0 else 1
            pv2_hist_ratio = pv2 / pv2_reference if pv2_reference > 0 else 1
            pv1_drop_pct = max(0, (1 - pv1_hist_ratio) * 100)
            pv2_drop_pct = max(0, (1 - pv2_hist_ratio) * 100)
            max_deviation_pct = max(max_deviation_pct, pv1_drop_pct, pv2_drop_pct)

            if pv1_reference > 1.0 and pv1 < 0.15:
                status = "CRITICAL"
                alert = "Possible defaut String PV1 : production quasi nulle par rapport a son historique"
                priority = 6
            elif pv2_reference > 1.0 and pv2 < 0.15:
                status = "CRITICAL"
                alert = "Possible defaut String PV2 : production quasi nulle par rapport a son historique"
                priority = 6
            elif pv1_drop_pct >= 45 and pv1_reference > 0.8:
                status = "WARNING"
                alert = "PV1 nettement sous son niveau habituel : verifier ombrage, connectique ou panneau"
                priority = max(priority, 5)
            elif pv2_drop_pct >= 45 and pv2_reference > 0.8:
                status = "WARNING"
                alert = "PV2 nettement sous son niveau habituel : verifier ombrage, connectique ou panneau"
                priority = max(priority, 5)

        # Expected string comparison with orientation awareness.
        if perf.get("pv1_expected_kw", 0.0) >= 0.5 and pv1_ratio > 0 and pv1_ratio < 60:
            status = "WARNING"
            alert = f"PV1 sous l'attendu pour son orientation SSO : {pv1_ratio} % du modele. Verifier ombrage ou connectique PV1."
            priority = max(priority, 5)
        if perf.get("pv2_expected_kw", 0.0) >= 0.5 and pv2_ratio > 0 and pv2_ratio < 60:
            status = "WARNING"
            alert = f"PV2 sous l'attendu pour son orientation sud : {pv2_ratio} % du modele. Verifier ombrage ou connectique PV2."
            priority = max(priority, 5)

        # Contextual normal orientation notes.
        if status == "OK" and pv1 > 0 and pv2 > 0:
            if sun_az < -20 and pv1 < pv2:
                alert = "PV1 inferieur a PV2 ce matin : coherent avec orientation sud-sud-ouest. Production globale conforme."
            elif sun_az > 20 and pv1 >= pv2:
                alert = "PV1 reprend l'avantage l'apres-midi : comportement coherent avec orientation sud-sud-ouest."
            elif perf_ratio >= 90:
                alert = f"Production PV conforme au modele saison/meteo : {perf_ratio} % de l'attendu."
            else:
                alert = "Strings PV conformes a leur comportement attendu."

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
            "pv_expected_kw": self._safe_round(expected_total, 2),
            "pv_performance_ratio_pct": self._safe_round(perf_ratio, 1),
            "pv1_expected_kw": perf.get("pv1_expected_kw", 0.0),
            "pv2_expected_kw": perf.get("pv2_expected_kw", 0.0),
            "pv1_performance_ratio_pct": self._safe_round(pv1_ratio, 1),
            "pv2_performance_ratio_pct": self._safe_round(pv2_ratio, 1),
            "solar_elevation_deg": self._safe_round(elevation, 1),
            "solar_array_azimuth_deg": self._safe_round(sun_az, 1),
        }

    def _estimate_pv_forecast(self, current_pv, weather_context=None):
        weather_context = weather_context or self._get_weather_context()
        now_hour = datetime.now().hour
        historical_now = self._average_pv_for_hour(now_hour)
        weather_factor = self._to_float(weather_context.get("factor"), 0.5)
        physics_perf = self._expected_pv_performance(0, 0, current_pv, weather_context)
        physics_estimate = physics_perf.get("pv_expected_kw", 0.0)
        history_estimate = historical_now * weather_factor if historical_now > 0 else 0.0
        pv_estimated_kw = max(current_pv, physics_estimate, history_estimate)
        return self._safe_round(max(0, pv_estimated_kw), 1)

    def _predict_pv_energy_next_hours(self, current_pv, hours, weather_context):
        now = datetime.now()
        weather_factor = self._to_float(weather_context.get("factor"), 0.5)
        total = 0.0
        used_history = False

        for index in range(hours):
            target_hour = (now.hour + index) % 24
            historical = self._average_pv_for_hour(target_hour)
            if historical > 0:
                total += historical * weather_factor
                used_history = True
            else:
                decay = max(0.35, 1.0 - 0.08 * index)
                total += max(current_pv, 0.0) * weather_factor * decay

        if not used_history and current_pv <= 0:
            return 0.0
        return self._safe_round(total, 2)

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
                      pv_forecast_kw, habit_load_now, habit_load_next_6h, predicted_pv_next_6h_kwh,
                      predicted_load_next_6h_kwh, estimated_autonomy_h, estimated_full_h,
                      pv_string_analysis, weather_context, power_limits_analysis):
        advice = []
        priority = 0
        pv_string_priority = pv_string_analysis.get("pv_string_priority", 0)
        pv_string_status = pv_string_analysis.get("pv_string_status", "OK")
        pv_string_alert = pv_string_analysis.get("pv_string_alert", "")
        weather_label = weather_context.get("label", "meteo inconnue")
        predicted_surplus_6h = predicted_pv_next_6h_kwh - predicted_load_next_6h_kwh
        current_surplus = max(0.0, pv_power - load_power)
        next_hours_good_for_load = (
            predicted_surplus_6h >= self.flexible_load_min_surplus_kw * self.flexible_load_min_duration_h
            or (current_surplus >= self.flexible_load_min_surplus_kw and pv_forecast_kw > habit_load_next_6h)
            or (isinstance(power_limits_analysis, dict) and power_limits_analysis.get("curtailment_risk"))
        )

        if pv_string_status in ["CRITICAL", "WARNING"]:
            advice.append(pv_string_alert)
            priority = max(priority, pv_string_priority)
        elif pv_string_status == "WATCH":
            advice.append(pv_string_alert)
            priority = max(priority, 3)

        limit_messages = power_limits_analysis.get("messages", []) if isinstance(power_limits_analysis, dict) else []
        for message in limit_messages[:2]:
            advice.append(message)
            priority = max(priority, 4)

        if isinstance(power_limits_analysis, dict) and power_limits_analysis.get("curtailment_risk"):
            flex_kw = power_limits_analysis.get("effective_flexible_load_kw", 0.0)
            if flex_kw >= 0.8 and tempo_today != 3:
                advice.append(f"Surplus possiblement bridé : lancer environ {flex_kw} kW d'usages flexibles peut améliorer l'autoconsommation.")
                priority = max(priority, 5)

        if tempo_tomorrow == 3:
            advice.append("Demain sera rouge : viser une batterie haute ce soir et activer Veille HC la nuit pour eviter de vider la batterie en heures creuses.")
            priority = max(priority, 7)
            if battery_soc < self.red_day_target_soc:
                advice.append(f"Objectif recommande avant demain matin : atteindre environ {int(self.red_day_target_soc)} % de batterie.")
                priority = max(priority, 7)
            if next_hours_good_for_load and tempo_today != 3:
                advice.append("Fenetre solaire favorable avant jour rouge : lancer maintenant ballon, lave-linge, lave-vaisselle ou recharge pilotable plutot que demain.")
                priority = max(priority, 6)
        elif tempo_tomorrow == 2:
            advice.append("Demain sera blanc : conserver une marge batterie et avancer les usages flexibles si le solaire est disponible aujourd'hui.")
            priority = max(priority, 4)
            if battery_soc < self.white_day_target_soc:
                advice.append(f"Objectif prudent : garder au moins {int(self.white_day_target_soc)} % de batterie avant demain matin.")
                priority = max(priority, 4)

        if tempo_today == 3:
            advice.append("Aujourd'hui est rouge : limiter les gros consommateurs, conserver la batterie pour les heures pleines et eviter l'import reseau.")
            priority = max(priority, 7)
            if grid_power > 0.1:
                advice.append("Import reseau detecte en jour rouge : couper ou reporter immediatement les charges non critiques.")
                priority = max(priority, 8)
        elif tempo_today == 2:
            advice.append("Tempo blanc aujourd'hui : privilegier les usages energivores pendant les periodes de surplus solaire.")
            priority = max(priority, 3)
        elif tempo_today == 1:
            if next_hours_good_for_load and battery_soc >= 50:
                advice.append(f"Tempo bleu et {weather_label} : surplus probable sur 6 h, bon moment pour lancer les appareils energivores pilotables.")
                priority = max(priority, 4)
            else:
                advice.append("Tempo bleu : jour favorable, surveiller le surplus solaire et charger la batterie sans contrainte forte.")
                priority = max(priority, 2)

        if battery_soc < self.low_soc_threshold:
            advice.append("Batterie faible : limiter la consommation non critique jusqu'au retour d'une production suffisante.")
            priority = max(priority, 6)
        elif battery_soc < 35 and tempo_tomorrow == 3:
            advice.append("Batterie trop basse avant un jour rouge : eviter toute decharge inutile et preparer la Veille HC.")
            priority = max(priority, 7)

        if pv_power > load_power and battery_soc < 95:
            advice.append("Production PV superieure a la maison : laisser charger la batterie en priorite.")
            priority = max(priority, 3)
        if pv_power > load_power and battery_soc >= 95:
            advice.append("Batterie presque pleine et surplus solaire : lancer les usages flexibles maintenant pour maximiser l'autoconsommation.")
            priority = max(priority, 4)

        if next_hours_good_for_load and tempo_today != 3 and battery_soc >= 60:
            advice.append(f"Prediction 6 h : PV estime {predicted_pv_next_6h_kwh} kWh vs conso habituelle {predicted_load_next_6h_kwh} kWh, usages energivores recommandes.")
            priority = max(priority, 4)
        elif predicted_surplus_6h < -1.0 and battery_soc < 60:
            advice.append(f"Prediction 6 h deficitaire : conso habituelle {predicted_load_next_6h_kwh} kWh superieure au PV prevu {predicted_pv_next_6h_kwh} kWh, conserver la batterie.")
            priority = max(priority, 4)

        if habit_load_next_6h > max(load_power, 0.1) * 1.25 and battery_soc < 50:
            advice.append("La consommation habituelle des prochaines heures est elevee : garder une reserve batterie.")
            priority = max(priority, 4)
        if pv_forecast_kw < 1 and battery_soc < 50:
            advice.append("Faible production solaire prevue : conserver la batterie et reporter les charges flexibles.")
            priority = max(priority, 4)
        if estimated_autonomy_h > 0 and estimated_autonomy_h < 3:
            advice.append(f"Autonomie batterie estimee faible : environ {estimated_autonomy_h} h au rythme actuel.")
            priority = max(priority, 4)
        if estimated_full_h > 0 and estimated_full_h <= 3:
            advice.append(f"Batterie probablement pleine dans environ {estimated_full_h} h : preparer les usages flexibles.")
            priority = max(priority, 2)

        if not advice:
            advice.append("Systeme optimal : aucune action particuliere recommandee.")
            priority = max(priority, 1)

        unique = []
        for item in advice:
            if item and item not in unique:
                unique.append(item)
        return self._limit_text(" ".join(unique[:3]), 240), priority

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

            weather_context = self._get_weather_context()
            pv_string_analysis = self._analyze_pv_strings(pv1_power, pv2_power, pv_total_dc_power, pv_power, weather_context)
            pv_forecast_kw = self._estimate_pv_forecast(pv_power, weather_context)
            power_limits_analysis = self._analyze_power_limits(
                pv_power=pv_power,
                pv_total_dc_power=pv_total_dc_power,
                load_power=load_power,
                battery_power=battery_power,
                grid_power=grid_power,
                battery_soc=battery_soc,
                pv_expected_kw=pv_string_analysis.get("pv_expected_kw", pv_forecast_kw),
            )
            habit_load_now = self._average_load_for_hour(datetime.now().hour)
            habit_load_next_6h = self._average_load_next_hours(6)
            predicted_load_next_6h_kwh = self._average_energy_next_hours("load_power", 6)
            predicted_pv_next_6h_kwh = self._predict_pv_energy_next_hours(pv_power, 6, weather_context)

            load_reference = max(load_power, habit_load_now, 0.1)
            estimated_autonomy_h = self._estimate_autonomy_hours(battery_soc, load_reference)
            estimated_full_h = self._estimate_full_charge_hours(battery_soc, battery_power, pv_power, load_power)
            energy_mode = self._detect_energy_mode(pv_power, load_power, battery_power, grid_power)

            advice, priority = self._build_advice(
                tempo_today, tempo_tomorrow, battery_soc, pv_power, load_power, grid_power,
                pv_forecast_kw, habit_load_now, habit_load_next_6h,
                predicted_pv_next_6h_kwh, predicted_load_next_6h_kwh,
                estimated_autonomy_h, estimated_full_h,
                pv_string_analysis, weather_context, power_limits_analysis,
            )

            if priority >= 6:
                confidence = "high"
            elif priority >= 3:
                confidence = "medium"
            else:
                confidence = "normal"

            predicted_surplus_6h = self._safe_round(predicted_pv_next_6h_kwh - predicted_load_next_6h_kwh, 2)
            pv_expected_kw = pv_string_analysis.get("pv_expected_kw", 0.0)
            pv_perf_pct = pv_string_analysis.get("pv_performance_ratio_pct", 0.0)
            limit_note = ""
            if power_limits_analysis.get("curtailment_risk"):
                limit_note = f" Limite injection/charge : {power_limits_analysis.get('effective_flexible_load_kw', 0)} kW flexibles utiles."
            elif power_limits_analysis.get("ac_clipping_risk"):
                limit_note = " Onduleur proche limite AC."

            prediction = (
                f"{energy_mode}. Meteo: {weather_context.get('label')}. "
                f"PV prevu maintenant: {pv_forecast_kw} kW. "
                f"Modele PV: {pv_expected_kw} kW / performance {pv_perf_pct} %. "
                f"Bilan estime 6 h: {predicted_surplus_6h} kWh. "
                f"Autonomie estimee: {estimated_autonomy_h} h."
                f"{limit_note}"
            )

            prediction = self._limit_text(prediction, 240)

            if tempo_tomorrow == 3 and battery_soc < self.red_day_target_soc:
                battery_strategy = f"Preparer jour rouge : viser {int(self.red_day_target_soc)} % et activer Veille HC"
            elif tempo_today == 3:
                battery_strategy = "Jour rouge : preserver la batterie et limiter l'import reseau"
            elif estimated_full_h > 0:
                battery_strategy = f"Charge complete estimee dans {estimated_full_h} h"
            elif battery_soc >= 95:
                battery_strategy = "Batterie presque pleine : favoriser les usages flexibles"
            elif battery_soc < 25:
                battery_strategy = "Preserver la batterie"
            else:
                battery_strategy = "Gestion batterie normale"

            battery_strategy = self._limit_text(battery_strategy, 180)
            energy_mode = self._limit_text(energy_mode, 120)
            pv_alert_text = self._limit_text(pv_string_analysis.get("pv_string_alert"), 240)

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
                "pv_string_alert": pv_alert_text,
                "pv_string_imbalance_pct": pv_string_analysis.get("pv_string_imbalance_pct"),
                "pv_expected_kw": pv_string_analysis.get("pv_expected_kw"),
                "pv_performance_ratio_pct": pv_string_analysis.get("pv_performance_ratio_pct"),
                "pv1_expected_kw": pv_string_analysis.get("pv1_expected_kw"),
                "pv2_expected_kw": pv_string_analysis.get("pv2_expected_kw"),
                "pv1_performance_ratio_pct": pv_string_analysis.get("pv1_performance_ratio_pct"),
                "pv2_performance_ratio_pct": pv_string_analysis.get("pv2_performance_ratio_pct"),
                "solar_elevation_deg": pv_string_analysis.get("solar_elevation_deg"),
                "solar_array_azimuth_deg": pv_string_analysis.get("solar_array_azimuth_deg"),
                "pv_ac_limit_kw": INVERTER_AC_POWER_LIMIT_KW,
                "battery_charge_limit_kw": BATTERY_CHARGE_LIMIT_KW,
                "grid_export_limit_kw": GRID_EXPORT_LIMIT_KW,
                "pv_ac_headroom_kw": power_limits_analysis.get("ac_headroom_kw"),
                "battery_charge_headroom_kw": power_limits_analysis.get("battery_charge_headroom_kw"),
                "grid_export_headroom_kw": power_limits_analysis.get("export_headroom_kw"),
                "pv_flexible_load_recommended_kw": power_limits_analysis.get("effective_flexible_load_kw"),
                "pv_curtailment_risk": bool(power_limits_analysis.get("curtailment_risk")),
                "pv_ac_clipping_risk": bool(power_limits_analysis.get("ac_clipping_risk")),
                "pv_dc_usable_clipping_risk": bool(power_limits_analysis.get("pv_dc_usable_clipping_risk")),
                "pv_dc_usable_limit_kw": PV_DC_USABLE_LIMIT_KW,
                "pv_dc_recommended_max_kw": PV_DC_RECOMMENDED_MAX_KW,
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


# Compatibility aliases for main.py.
AIEngine = AiEngine
AIEnergyEngine = AiEngine
SolidAIEngine = AiEngine
EnergyAIEngine = AiEngine
