import base64
import hashlib
import hmac
import json
import os
import time
from email.utils import formatdate

import requests


class SolisClient:
    def __init__(self):
        self.key_id = os.getenv("SOLIS_KEY_ID")
        self.key_secret = os.getenv("SOLIS_KEY_SECRET")

        # Optional manual override if needed
        self.inverter_id = os.getenv("SOLIS_INVERTER_ID")

        self.base_url = "https://www.soliscloud.com:13333"

        self.last_autodetect_attempt = 0
        self.autodetect_retry_interval = 300
        self.timeout = 20

        if not self.inverter_id:
            self.inverter_id = self._get_valid_inverter()

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
                timeout=self.timeout,
            )

            if response.status_code != 200:
                print(f"HTTP {response.status_code}: {response.text}", flush=True)
                return None

            return response.json()

        except Exception as error:
            print("HTTP ERROR:", error, flush=True)
            return None

    def _to_float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _map_data(self, d):
        # Solis:
        # pac = puissance AC instantanee onduleur en kW
        # familyLoadPower = consommation maison instantanee en kW
        # batteryPower positif semble correspondre a une charge batterie
        # psum negatif semble correspondre a une injection reseau

        pv_power = d.get("pac")
        if pv_power is None:
            pv_power = d.get("power", 0)

        home_load = d.get("familyLoadPower")
        if home_load is None:
            home_load = d.get("totalLoadPower")
        if home_load is None:
            home_load = d.get("consumptionPower", 0)

        battery_power_raw = self._to_float(d.get("batteryPower"))

        # Pour Power Flow Card Plus:
        # valeur positive = batterie qui decharge
        # valeur negative = batterie qui charge
        battery_flow_power = -battery_power_raw

        result = {
            "pv_power": self._to_float(pv_power),
            "battery_soc": self._to_float(d.get("batteryCapacitySoc")),
            "grid_power": self._to_float(d.get("psum")),
            "load_power": self._to_float(home_load),
            "battery_power": battery_power_raw,
            "battery_flow_power": battery_flow_power,
            "daily_energy": self._to_float(d.get("etoday", d.get("eToday"))),
            "total_energy": self._to_float(d.get("etotal", d.get("eTotal"))),
            "inverter_temp": self._to_float(d.get("temperature")),
        }

        return result

    def _get_inverter_list(self):
        payload = {
            "pageNo": 1,
            "pageSize": 10,
        }

        data = self._post("/v1/api/inverterList", payload)

        if not data:
            print("Cannot fetch inverter list: no response", flush=True)
            return []

        if not data.get("success"):
            print("Cannot fetch inverter list:", data, flush=True)
            return []

        try:
            records = data["data"]["page"]["records"]

            if not records:
                print("No inverter found in inverter list", flush=True)
                return []

            return records

        except Exception as error:
            print("Inverter list parsing error:", error, flush=True)
            return []

    def _get_valid_inverter(self):
        now = time.time()

        if now - self.last_autodetect_attempt < self.autodetect_retry_interval:
            return None

        self.last_autodetect_attempt = now

        print("Auto-detect inverter...", flush=True)

        records = self._get_inverter_list()

        if not records:
            print("Auto-detect failed: no inverter list", flush=True)
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

    def _get_data_from_inverter_list(self):
        records = self._get_inverter_list()

        if not records:
            return {}

        inverter = records[0]

        if not self.inverter_id:
            detected_id = inverter.get("id") or inverter.get("inverterId")
            if detected_id:
                self.inverter_id = str(detected_id)
                print(f"Inverter ID recovered from list: {self.inverter_id}", flush=True)

        result = self._map_data(inverter)

        print("DATA from inverter list fallback:", result, flush=True)

        return result

    def get_data(self):
        try:
            if not self.inverter_id:
                print("No inverter ID available, retrying auto-detect...", flush=True)
                self.inverter_id = self._get_valid_inverter()

            if not self.inverter_id:
                print("No inverter ID after retry, using list fallback...", flush=True)
                return self._get_data_from_inverter_list()

            payload = {
                "id": self.inverter_id,
            }

            data = self._post("/v1/api/inverterDetail", payload)

            if not data:
                print("API returned None, using list fallback...", flush=True)
                return self._get_data_from_inverter_list()

            if not data.get("success"):
                print("API error:", data, flush=True)
                return self._get_data_from_inverter_list()

            d = data.get("data")

            if not d:
                print("Empty inverter detail data, using list fallback...", flush=True)
                return self._get_data_from_inverter_list()

            result = self._map_data(d)

            print("DATA:", result, flush=True)

            return result

        except Exception as error:
            print("ERROR SOLIS:", error, flush=True)
            return self._get_data_from_inverter_list()
