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
