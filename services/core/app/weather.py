import requests


class Weather:
    def __init__(self):
        # 👉 adapte coord GPS (important)
        self.lat = 50.29   # exemple nord France
        self.lon = 2.78

    def get_forecast(self):
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={self.lat}"
                f"&longitude={self.lon}"
                f"&hourly=cloudcover,shortwave_radiation"
            )

            r = requests.get(url, timeout=5)
            data = r.json()

            radiation = data["hourly"]["shortwave_radiation"][0]
            cloud = data["hourly"]["cloudcover"][0]

            return {
                "radiation": radiation,
                "cloud": cloud,
            }

        except Exception:
            return {
                "radiation": 0,
                "cloud": 100,
            }
