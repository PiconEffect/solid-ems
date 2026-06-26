from tempo import Tempo


class AiEngine:
    def __init__(self):
        self.tempo = Tempo()

    def analyze(self, data):
        pv = data.get("pv_power", 0)
        load = data.get("load_power", 0)
        battery = data.get("battery_soc", 0)
        grid = data.get("grid_power", 0)

        tempo_day = self.tempo.get_tempo()

        advice = "✅ Système optimal"

        # -----------------------------
        # 🔵 Gestion Tempo
        # -----------------------------
        if tempo_day == "ROUGE":
            if battery < 80:
                advice = "🔴 Tempo rouge : conserve batterie"
            else:
                advice = "🔴 Tempo rouge : autonomie batterie OK"

        elif tempo_day == "BLEU":
            if pv > load:
                advice = "🔵 Tempo bleu : consomme librement"
            else:
                advice = "🔵 Tempo bleu : tarif avantageux"

        # -----------------------------
        # ⚡ Logique énergétique
        # -----------------------------
        if pv > load and battery > 70:
            advice = "☀️ Surplus solaire : lance machines maintenant"

        if battery < 20:
            advice = "⚠️ Batterie faible : limiter consommation"

        if grid < -500:
            advice = "💡 Injection réseau : améliorer autoconsommation"

        # -----------------------------
        # 🔋 Mini prédiction simple
        # -----------------------------
        predicted_full = None

        if pv > 2000 and battery < 90:
            predicted_full = "≈ Batterie pleine dans 2-4h"

        return {
            "advice": advice,
            "tempo": tempo_day,
            "prediction": predicted_full if predicted_full else "N/A",
        }
