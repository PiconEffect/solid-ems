import time

import requests


class Tempo:
    def __init__(self):
        self.base_url = "https://www.api-couleur-tempo.fr/api/jourTempo"
        self.cache_duration = 900
        self.last_update = 0
        self.cached_data = {
            "tempo": 0,
            "tempo_label": "Inconnu",
            "tempo_tomorrow": 0,
            "tempo_tomorrow_label": "Inconnu",
        }

    def _normalize_code(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _fetch_day(self, day):
        url = f"{self.base_url}/{day}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"Tempo HTTP {response.status_code}: {response.text}", flush=True)
                return {
                    "code": 0,
                    "label": "Inconnu",
                }

            data = response.json()

            return {
                "code": self._normalize_code(data.get("codeJour")),
                "label": data.get("libCouleur", "Inconnu"),
            }

        except Exception as error:
            print("Tempo API error:", error, flush=True)
            return {
                "code": 0,
                "label": "Inconnu",
            }

    def get_tempo_data(self):
        now = time.time()

        if now - self.last_update < self.cache_duration:
            return self.cached_data

        today = self._fetch_day("today")
        tomorrow = self._fetch_day("tomorrow")

        self.cached_data = {
            "tempo": today["code"],
            "tempo_label": today["label"],
            "tempo_tomorrow": tomorrow["code"],
            "tempo_tomorrow_label": tomorrow["label"],
        }

        self.last_update = now

        print("Tempo data:", self.cached_data, flush=True)

        return self.cached_data

    def get_tempo(self):
        return self.get_tempo_data().get("tempo", 0)

    def get_tempo_tomorrow(self):
        return self.get_tempo_data().get("tempo_tomorrow", 0)
