import requests
import time
import hashlib
import base64
import hmac
import os
import json
from email.utils import formatdate


class SolisClient:
    def __init__(self):
        self.key_id = os.getenv("SOLIS_KEY_ID")
        self.key_secret = os.getenv("SOLIS_KEY_SECRET")
        self.inverter_id = os.getenv("SOLIS_INVERTER_ID")

        self.base_url = "https://www.soliscloud.com:13333"

    # -------------------------
    # 🔐 SIGNATURE API SOLIS
    # -------------------------
    def _sign(self, body, date, endpoint):
        # MD5 du body encodé base64
        content_md5 = base64.b64encode(
            hashlib.md5(body.encode("utf-8")).digest()
        ).decode()

        # String à signer
        sign_str = f"POST\n{content_md5}\napplication/json\n{date}\n{endpoint}"

        # Signature HMAC SHA1
        signature = base64.b64encode(
            hmac.new(
                self.key_secret.encode(),
                sign_str.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        return content_md5, signature

    # -------------------------
    # 📡 REQUETE POST SECURISEE
    # -------------------------
    def _post(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"

        body = json.dumps(payload)

        # Date format RFC (obligatoire pour Solis)
        date = formatdate(usegmt=True)

        # Génération signature
        content_md5, signature = self._sign(body, date, endpoint)

        headers = {
            "Content-Type": "application/json",
            "Content-MD5": content_md5,
            "Date": date,
            "Authorization": f"API {self.key_id}:{signature}",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=body,
                timeout=10
            )
            return response.json()

        except Exception as e:
            print("❌ HTTP ERROR:", e)
            return {}

    # -------------------------
    # ⚡ RECUPERATION DONNEES
    # -------------------------
    def get_data(self):
        try:
            if not self.inverter_id:
                print("❌ Missing SOLIS_INVERTER_ID")
                return {}

            payload = {
                "id": self.inverter_id
            }

            data = self._post("/v1/api/inverterDetail", payload)

            if not data.get("success"):
                print("❌ API error:", data)
                return {}

            d = data.get("data", {})

            result = {
                "pv_power": d.get("power", 0),
                "battery_soc": d.get("batteryCapacitySoc", 0),
                "grid_power": d.get("psum", 0),
                "load_power": d.get("consumptionPower", 0),
                "battery_power": d.get("batteryPower", 0),
                "daily_energy": d.get("eToday", 0),
                "total_energy": d.get("eTotal", 0),
                "inverter_temp": d.get("temperature", 0),
            }

            print("✅ DATA:", result)

            return result

        except Exception as e:
            print("❌ ERROR SOLIS:", e)
            return {}
