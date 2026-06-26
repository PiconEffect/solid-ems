from tempo import Tempo
from weather import Weather


class AiEngine:
    def __init__(self):
        self.tempo = Tempo()
        self.weather = Weather()

    def analyze(self, data):
        pv = data.get("pv_power", 0)
        load = data.get("load_power", 0)
        battery = data.get("battery_soc", 0)

        tempo_day = self.tempo.get_tempo()
        weather = self.weather.get_forecast()

        radiation = weather["radiation"]
        cloud = weather["cloud"]

        # -----------------------
        # ☀️ estimation PV simple
        # -----------------------
        pv_forecast = radiation * (1 - cloud / 100)

        # normalisation approximative
        pv_estimated_kw = round(pv_forecast / 200, 1)

        # -----------------------
        # 🔋 prédiction batterie
        # -----------------------
        prediction = "N/A"

        if pv_estimated_kw > 3:
            prediction = "🔋 Batterie pleine vers midi"
        elif pv_estimated_kw > 1:
            prediction = "🔋 Charge partielle batterie"
        else:
            prediction = "⚠️ Faible production solaire"

        # -----------------------
        # 💡 conseil intelligent
        # -----------------------
        advice = "✅ Système optimal"

        if tempo_day == "ROUGE":
            advice = "🔴 Tempo rouge : éviter consommation"

        elif tempo_day == "BLEU" and pv_estimated_kw > 3:
            advice = "☀️ Idéal pour lancer appareils"

        if battery < 20:
            advice = "⚠️ Batterie faible"

        if pv > load and battery > 70:
            advice = "🔥 Surplus solaire : consommer maintenant"

        return {
            "advice": advice,
            "tempo": tempo_day,
            "pv_forecast_kw": pv_estimated_kw,
            "prediction": prediction,
        }
