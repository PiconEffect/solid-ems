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

        self.inverter_id = self._get_valid_inverter()

    # -------------------------
    # API SIGNATURE
    # -------------------------
    def _sign(self, body, date, endpoint):
        content_md5 = base64.b64encode(
            hashlib.md5(body.encode("utf-8")).digest()
        ).decode()

        sign_str = f"POST\n{content_md5}\napplication/json\n{date}\n{endpoint}"

        signature = base64.b64encode(
            hmac.new(
                self.key_secret.encode(),
                sign_str.encode(),
                hashlib.sha1,
            ).digest()
        ).decode()

        return content_md5, signature

    # -------------------------
    # API POST
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
            response = requests.post(
                url,
                headers=headers,
                data=body,
                timeout=10,
            )

            if response.status_code != 200:
                print(f"HTTP {response.status_code}: {response.text}", flush=True)
                return None

            return response.json()

        except Exception as error:
            print("HTTP ERROR:", error, flush=True)
            return None

    # -------------------------
    # AUTO-DETECT INVERTER
    # -------------------------
    def _get_valid_inverter(self):
        print("Auto-detect inverter...", flush=True)

        payload = {
            "pageNo": 1,
            "pageSize": 10,
        }

        data = self._post("/v1/api/inverterList", payload)

        if not data or not data.get("success"):
            print("Cannot fetch inverter list:", data, flush=True)
            return None

        try:
            records = data["data"]["page"]["records"]

            if not records:
                print("No inverter found", flush=True)
                return None

            print("RAW inverter list:", records, flush=True)

            for inverter in records:
                possible_ids = [
                    inverter.get("id"),
                    inverter.get("inverterId"),
                    inverter.get("sn"),
                    inverter.get("deviceSn"),
                    inverter.get("inverterSn"),
                ]

                for inverter_id in possible_ids:
                    if not inverter_id:
                        continue

                    print(f"Testing inverter ID: {inverter_id}", flush=True)

                    test = self._post(
                        "/v1/api/inverterDetail",
                        {"id": inverter_id},
                    )

                    if test and test.get("success") and test.get("data"):
                        print(f"VALID inverter found: {inverter_id}", flush=True)
                        return str(inverter_id)

            print("No valid inverter working", flush=True)
            return None

        except Exception as error:
            print("Inverter parsing error:", error, flush=True)
            return None

    # -------------------------
    # SAFE FLOAT
    # -------------------------
    def _to_float(self, value, default=0):
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    # -------------------------
    # GET LIVE DATA
    # -------------------------
    def get_data(self):
        try:
            if not self.inverter_id:
                print("No inverter ID available", flush=True)
                return {}

            payload = {
                "id": self.inverter_id,
            }

            data = self._post("/v1/api/inverterDetail", payload)

            if not data:
                print("API returned None", flush=True)
                return {}

            if not data.get("success"):
                print("API error:", data, flush=True)
                return {}

            d = data.get("data")

            if not d:
                print("Empty data:", data, flush=True)
                return {}

            # --------------------------------------------------
            # SOLIS MAPPING
            #
            # pac = puissance instantanée AC onduleur en kW
            # power = souvent puissance nominale / valeur moins fiable
            # pow1 + pow2 = puissance DC MPPT, utile mais pas toujours égale AC
            # familyLoadPower = vraie consommation maison instantanée en kW
            # totalLoadPower = autre valeur maison, souvent identique
            # psum = puissance réseau en kW
            # batteryPower = puissance batterie en kW
            # --------------------------------------------------

            pv_power = d.get("pac")
            if pv_power is None:
                pv_power = d.get("power", 0)

            load_power = d.get("familyLoadPower")
            if load_power is None:
                load_power = d.get("totalLoadPower")
            if load_power is None:
                load_power = d.get("consumptionPower", 0)

            result = {
                "pv_power": self._to_float(pv_power),
                "battery_soc": self._to_float(d.get("batteryCapacitySoc")),
                "grid_power": self._to_float(d.get("psum")),
                "load_power": self._to_float(load_power),
                "battery_power": self._to_float(d.get("batteryPower")),
                "daily_energy": self._to_float(d.get("etoday", d.get("eToday"))),
                "total_energy": self._to_float(d.get("etotal", d.get("eTotal"))),
                "inverter_temp": self._to_float(d.get("temperature")),
            }

            print("DATA:", result, flush=True)

            return result

        except Exception as error:
            print("ERROR SOLIS:", error, flush=True)
            return {}
