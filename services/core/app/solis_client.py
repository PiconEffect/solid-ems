import requests
import os
import time


class SolisClient:
    def __init__(self):
        self.username = os.getenv("SOLIS_USERNAME")
        self.password = os.getenv("SOLIS_PASSWORD")

        self.base_url = "https://www.soliscloud.com:13333"

        self.token = None
        self.token_expiry = 0

        self.plant_id = None
        self.inverter_id = None

    # -----------------------
    # AUTHENTIFICATION
    # -----------------------
    def login(self):
        url = f"{self.base_url}/v1/api/userLogin"

        payload = {
            "userInfo": self.username,
            "password": self.password,
        }

        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if data.get("success"):
            self.token = data["data"]["token"]
            self.token_expiry = time.time() + 3500
            print("✅ Solis login OK")
        else:
            print("❌ Login failed:", data)

    def ensure_token(self):
        if not self.token or time.time() > self.token_expiry:
            self.login()

    # -----------------------
    # PLANT
    # -----------------------
    def get_plant(self):
        self.ensure_token()

        url = f"{self.base_url}/v1/api/plantList"
        headers = {"Authorization": self.token}

        response = requests.post(url, headers=headers, timeout=10)
        data = response.json()

        if data.get("success") and data["data"]["page"]["records"]:
            plant = data["data"]["page"]["records"][0]
            self.plant_id = plant["id"]
            return plant

        print("❌ Failed to get plant:", data)
        return None

    # -----------------------
    # INVERTER
    # -----------------------
    def get_inverter(self):
        if not self.plant_id:
            self.get_plant()

        url = f"{self.base_url}/v1/api/inverterList"
        headers = {"Authorization": self.token}
        payload = {"plantId": self.plant_id}

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()

        if data.get("success") and data["data"]["page"]["records"]:
            inverter = data["data"]["page"]["records"][0]
            self.inverter_id = inverter["id"]
            return inverter

        print("❌ Failed to get inverter:", data)
        return None

    # -----------------------
    # DATA
    # -----------------------
    def get_data(self):
        try:
            self.ensure_token()

            if not self.inverter_id:
                self.get_inverter()

            if not self.inverter_id:
                return {}

            url = f"{self.base_url}/v1/api/inverterDetail"
            headers = {"Authorization": self.token}
            payload = {"id": self.inverter_id}

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()

            if not data.get("success"):
                print("❌ API error:", data)
                return {}

            d = data["data"]

            return {
                "pv_power": d.get("power", 0),
                "battery_soc": d.get("batteryCapacitySoc", 0),
                "grid_power": d.get("psum", 0),
                "load_power": d.get("consumptionPower", 0),
                "battery_power": d.get("batteryPower", 0),
                "daily_energy": d.get("eToday", 0),
                "total_energy": d.get("eTotal", 0),
                "inverter_temp": d.get("temperature", 0),
            }

        except Exception as e:
            print("❌ ERROR SOLIS:", e)
            return {}
