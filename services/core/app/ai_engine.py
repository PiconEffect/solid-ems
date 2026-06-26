class AiEngine:

    def analyze(self, data):
        advice = []

        pv = data.get("pv_power", 0)
        load = data.get("load_power", 0)
        battery = data.get("battery_soc", 0)
        grid = data.get("grid_power", 0)

        # ✅ Surproduction
        if pv > load and battery > 80:
            advice.append("✅ Surplus solaire : lance appareils énergivores")

        # ✅ Batterie faible
        if battery < 20:
            advice.append("⚠️ Batterie faible : limiter consommation")

        # ✅ Injection réseau
        if grid < -500:
            advice.append("💡 Injection réseau forte : optimiser autoconsommation")

        # ✅ Charge batterie
        if battery < 50 and pv > 2000:
            advice.append("🔋 Bonne production : batterie en charge efficace")

        if not advice:
            advice.append("✅ Système optimal")

        return {
            "advice": advice[0]  # version simple (1 message)
        }
