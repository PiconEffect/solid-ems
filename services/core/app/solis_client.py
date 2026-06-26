import requests
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
        self.inverter_id = None

        self.base_url = "https://www.soliscloud.com:13333"

        # ✅ AUTO-DETECT
        self.inverter_id = self._get_valid_inverter()

    # -------------------------
    # 🔐 SIGNATURE
    # -------------------------
    def _sign(self, body, date, endpoint):
        content_md5 = base64.b64encode(
            hashlib.md5(body.encode("utf-8")).digest()
        ).decode()

        sign_str = f"POST\n{content_md5}\napplication/json\n{date}\n{endpoint}"

        signature = base64.b64encode(
            hmac.new(self.key_secret.encode(), sign_str.encode(), hashlib.sha1).digest()
        ).decode()

        return content_md5, signature

    # -------------------------
    # 📡 POST API
    # -------------------------
    def _post(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"

        body = json.dumps(payload)
        date = formatdate(usegmt=True)

        content_md5, signature = self._sign(body, date, endpoint)

        headers = {
            "Content-Type": "application/json",
            "Content-MD5": content_md5,
            "Date": date,
            "Authorization": f"API {self.key_id}:{signature}",
        }

        try:
            response = requests.post(url, headers=headers, data=body, timeout=10)

            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return None

            return response.json()

        except Exception as e:
            print("❌ HTTP ERROR:", e)
            return None

    # -------------------------
    # 🔍 AUTO-DETECT + VALIDATION
    # -------------------------
    def _get_valid_inverter(self):
        print("🔍 Auto-detect inverter...")

        payload = {"pageNo": 1, "pageSize": 10}
        data = self._post("/v1/api/inverterList", payload)

        if not data or not data.get("success"):
            print("❌ Cannot fetch inverter list:", data)
            return None

        try:
            records = data["data"]["page"]["records"]

            if not records:
                print("❌ No inverter found")
                return None

            print("🔍 RAW inverter list:", records)

            # 🔥 TEST CHAQUE ID POSSIBLE
            for inv in records:
                possible_ids = [
                    inv.get("id"),
                    inv.get("sn"),
                    inv.get("deviceSn"),
                    inv.get("inverterSn"),
                ]

                for pid in possible_ids:
                    if not pid:
                        continue

                    print(f"🔍 Testing ID: {pid}")

                    test = self._post("/v1/api/inverterDetail", {"id": pid})

                    if test and test.get("success") and test.get("data"):
                        print(f"✅ VALID inverter found: {pid}")
                        return str(pid)

            print("❌ No valid inverter working")
            return None

        except Exception as e:
            print("❌ Parsing error:", e)
            return None

    # -------------------------
    # ⚡ DATA
    # -------------------------
    def get_data(self):
        try:
            if not self.inverter_id:
                print("❌ No inverter ID available")
                return {}

            payload = {"id": self.inverter_id}
            data = self._post("/v1/api/inverterDetail", payload)

            if not data:
                print("❌ API returned None")
                return {}

            if not data.get("success"):
                print("❌ API error:", data)
                return {}

            d = data.get("data")

            if not d:
                print("⚠️ Empty data:", data)
                return {}

            result = {
                "pv_power": d.get("power", 0),
                "battery_soc": d.get("batteryCapacitySoc", 0),
                "grid_power": d.get("psum", 0),
                "load_power": d.get("familyLoadPower", 0),
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
