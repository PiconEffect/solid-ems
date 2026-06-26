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
            "password": self.password
        }

        response = requests.post(url, json=payload).json()

        if response.get("success"):
            self.token = response["data"]["token"]
            self.token_expiry = time.time() + 3600
        else:
            raise Exception("❌ Login Solis failed")

    def ensure_token(self):
        if not self.token or time.time() > self.token_expiry:
            self.login()

    # -----------------------
    # RÉCUPÉRATION PLANT
    # -----------------------
    def get_plant(self):
        self.ensure_token()

        url = f"{self.base_url}/v1/api/plantList"

        headers = {"Authorization": self.token}

        response = requests.post(url, headers=headers).json()

        if response.get("success"):
            plant = response["data"]["page"]["records"][0]
            self.plant_id = plant["id"]
            return plant
        else:
            raise Exception("❌ Failed to get plant")

    # -----------------------
    # RÉCUPÉRATION INVERTER
    # -----------------------
    def get_inverter(self):
        if not self.plant_id:
            self.get_plant()

        url = f"{self.base_url}/v1/api/inverterList"

        headers = {"Authorization": self.token}

        payload = {"plantId": self.plant_id}

        response = requests.post(url, headers=headers, json=payload).json()

        if response.get("success"):
            inverter = response["data"]["page"]["records"][0]
            self.inverter_id = inverter["id"]
            return inverter
        else:
            raise Exception("❌ Failed to get inverter")

    # -----------------------
    # DATA TEMPS RÉEL
    # -----------------------
    def get_data(self):
        self.ensure_token()

        if not self.inverter_id:
            self.get_inverter()

        url = f"{self.base_url}/v1/api/inverterDetail"

        headers = {"Authorization": self.token}

        payload = {"id": self.inverter_id}

        response = requests.post(url, headers=headers, json=payload).json()

        if not response.get("success"):
            raise Exception("❌ Failed to get data")

        data = response["data"]

        # -----------------------
        # Mapping vers MQTT
        # -----------------------
        return {
            "pv_power": data.get("power", 0),
            "battery_soc": data.get("batteryCapacitySoc", 0),
            "grid_power": data.get("psum", 0),
            "load_power": data.get("consumptionPower", 0),
            "battery_power": data.get("batteryPower", 0),
            "daily_energy": data.get("eToday", 0),
            "total_energy": data.get("eTotal", 0),
            "inverter_temp": data.get("temperature", 0)
        }
