import requests


class Tempo:
    def get_tempo(self):
        try:
            url = "https://www.api-couleur-tempo.fr/api/jourTempo/today"
            r = requests.get(url, timeout=5)
            data = r.json()

            return data.get("codeJour", "UNKNOWN")

        except Exception:
            return "UNKNOWN"
