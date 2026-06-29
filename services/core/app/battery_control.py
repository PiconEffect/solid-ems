import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone


class BatteryControl:
    def __init__(self, inverter_sn=None):
        self.key_id = os.getenv("SOLIS_KEY_ID")
        self.key_secret = os.getenv("SOLIS_KEY_SECRET")

        self.user_name = os.getenv("SOLIS_USER_NAME")
        self.password = os.getenv("SOLIS_PASSWORD")

        self.inverter_sn = inverter_sn or os.getenv("SOLIS_INVERTER_SN")

        self.base_url = "https://www.soliscloud.com:13333"
        self.content_type = os.getenv("SOLIS_CONTROL_CONTENT_TYPE", "application/json")

        self.language = os.getenv("SOLIS_CONTROL_LANGUAGE", "2")

        self.dry_run = (
            os.getenv("SOLIS_CONTROL_DRY_RUN", "true").lower()
            in ["1", "true", "yes", "on"]
        )

        self.token = None
        self.token_time = 0
        self.token_validity_s = 3600

        self.cid_time_of_use_select = 100
        self.cid_allow_grid_charging = 109
        self.cid_storage_control_switching = 636
        self.cid_new_earning_marker = 6798
        self.cid_charge_discharge_one_cid = 6972

        self.last_6972_value = None
        self.last_6972_backup_time = None

        print(
            f"BATTERY CONTROL initialized dry_run={self.dry_run} inverter_sn={self._safe(self.inverter_sn)}",
            flush=True,
        )

    def _safe(self, value):
        if value is None:
            return ""
        value = str(value)
        if len(value) <= 4:
            return "****"
        return value[:2] + "****" + value[-2:]

    def _mask_payload(self, payload):
        if not isinstance(payload, dict):
            return payload

        masked = dict(payload)

        for key in ["passWord", "password", "SOLIS_PASSWORD"]:
            if key in masked:
                masked[key] = "********"

        return masked

    def update_inverter_sn(self, inverter_sn):
        if inverter_sn and inverter_sn != self.inverter_sn:
            self.inverter_sn = inverter_sn
            print(
                f"BATTERY CONTROL inverter SN updated: {self._safe(self.inverter_sn)}",
                flush=True,
            )

    def _now_gmt(self):
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    def _content_md5(self, body):
        return base64.b64encode(
            hashlib.md5(body.encode("utf-8")).digest()
        ).decode("utf-8")

    def _sign(self, body, date, endpoint):
        md5_value = self._content_md5(body)

        encrypt_str = (
            "POST"
            + "\n"
            + md5_value
            + "\n"
            + self.content_type
            + "\n"
            + date
            + "\n"
            + endpoint
        )

        signature = base64.b64encode(
            hmac.new(
                self.key_secret.encode("utf-8"),
                encrypt_str.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf-8")

        return md5_value, signature

    def _post(self, endpoint, payload, token=None):
        import requests

        if not self.key_id or not self.key_secret:
            print("BATTERY CONTROL API blocked: missing key id/secret", flush=True)
            return None

        body = json.dumps(payload)
        date = self._now_gmt()

        md5_value, signature = self._sign(body, date, endpoint)

        headers = {
            "Content-MD5": md5_value,
            "Content-Type": self.content_type,
            "Date": date,
            "Authorization": f"API {self.key_id}:{signature}",
        }

        if token:
            headers["Token"] = token

        url = f"{self.base_url}{endpoint}"

        try:
            print(
                f"BATTERY CONTROL POST {endpoint} payload={self._mask_payload(payload)}",
                flush=True,
            )

            response = requests.post(
                url,
                headers=headers,
                data=body,
                timeout=20,
            )

            if response.status_code != 200:
                print(
                    f"BATTERY CONTROL HTTP {response.status_code}: {response.text}",
                    flush=True,
                )
                return None

            try:
                return response.json()
            except Exception:
                print(
                    f"BATTERY CONTROL invalid JSON response: {response.text}",
                    flush=True,
                )
                return None

        except Exception as error:
            print("BATTERY CONTROL HTTP ERROR:", error, flush=True)
            return None

    def login(self):
        if not self.user_name or not self.password:
            print(
                "BATTERY CONTROL login skipped: missing SOLIS_USER_NAME or SOLIS_PASSWORD",
                flush=True,
            )
            return None

        now = time.time()

        if self.token and (now - self.token_time) < self.token_validity_s:
            return self.token

        md5_password = hashlib.md5(
            self.password.encode("utf-8")
        ).hexdigest()

        payload = {
            "userInfo": self.user_name,
            "passWord": md5_password,
        }

        data = self._post("/v2/api/login", payload)

        if not data:
            print("BATTERY CONTROL login failed: no response", flush=True)
            return None

        if not data.get("success"):
            print("BATTERY CONTROL login failed:", data, flush=True)
            return None

        token = None

        body = data.get("data")

        if isinstance(body, dict):
            token = (
                body.get("token")
                or body.get("Token")
                or body.get("accessToken")
                or body.get("access_token")
            )

        if not token:
            token = data.get("token") or data.get("Token")

        if not token:
            print("BATTERY CONTROL login failed: token not found in response", flush=True)
            print("BATTERY CONTROL login response:", data, flush=True)
            return None

        self.token = token
        self.token_time = now

        print("BATTERY CONTROL login OK, token received", flush=True)

        return self.token

    def set_current_6972_value(self, value):
        if not value:
            return

        self.last_6972_value = str(value)
        self.last_6972_backup_time = time.time()

        print("BATTERY CONTROL 6972 backup updated", flush=True)

    def split_6972_groups(self, value):
        if not value:
            return []

        parts = [p.strip() for p in str(value).split(",")]

        if len(parts) % 5 != 0:
            print(
                f"BATTERY CONTROL WARNING: 6972 value has {len(parts)} fields, expected multiple of 5",
                flush=True,
            )

        groups = []

        for index in range(0, len(parts), 5):
            group = parts[index:index + 5]
            if len(group) == 5:
                groups.append(group)

        return groups

    def join_6972_groups(self, groups):
        flat = []

        for group in groups:
            flat.extend(group)

        return ",".join(flat)

    def default_6972_value_all_off(self):
        groups = []

        for _ in range(12):
            groups.append([
                "0",
                "00:00-00:00",
                "0",
                "20",
                "48",
            ])

        return self.join_6972_groups(groups)

    def build_inhibit_6972_value(self, current_value):
        if not current_value:
            print(
                "BATTERY CONTROL no current 6972 value available, using all-off dry-run template",
                flush=True,
            )
            return self.default_6972_value_all_off()

        groups = self.split_6972_groups(current_value)

        if len(groups) < 12:
            print(
                f"BATTERY CONTROL WARNING: 6972 has {len(groups)} groups, expected 12",
                flush=True,
            )

        new_groups = []

        for index, group in enumerate(groups):
            new_group = list(group)

            # CID 6972 order from manufacturer:
            # groups 1 to 6 = charge slots
            # groups 7 to 12 = discharge slots
            # Each group = switch, time slot, current, SOC, voltage.
            if index >= 6:
                new_group[0] = "0"
                new_group[1] = "00:00-00:00"

            new_groups.append(new_group)

        return self.join_6972_groups(new_groups)

    def handle_command(self, command):
        print("BATTERY CONTROL command received:", command, flush=True)

        if not isinstance(command, dict):
            print("BATTERY CONTROL ignored: command is not a dict", flush=True)
            return

        action = command.get("action")
        mode = command.get("mode", "manual")
        enabled = command.get("enabled")
        duration_h = command.get("duration_h")

        if action == "inhibit_discharge" or enabled is True:
            self.inhibit_discharge(mode=mode, duration_h=duration_h)
            return

        if action == "resume_discharge" or enabled is False:
            self.resume_discharge(mode=mode)
            return

        if action == "arm_inhibit_discharge":
            print("BATTERY CONTROL armed for off-peak window", flush=True)
            return

        print("BATTERY CONTROL unsupported command:", command, flush=True)

    def inhibit_discharge(self, mode="manual", duration_h=None):
        print(
            f"BATTERY CONTROL inhibit discharge requested mode={mode} duration_h={duration_h}",
            flush=True,
        )

        new_value = self.build_inhibit_6972_value(self.last_6972_value)

        payload = {
            "cid": str(self.cid_charge_discharge_one_cid),
            "inverterSn": self.inverter_sn,
            "value": new_value,
            "yuanzhi": self.last_6972_value or new_value,
            "language": self.language,
        }

        if self.dry_run:
            print("BATTERY CONTROL DRY-RUN: no Solis command sent", flush=True)
            print("BATTERY CONTROL DRY-RUN payload:", payload, flush=True)
            return

        if not self.inverter_sn:
            print("BATTERY CONTROL blocked: missing inverter SN", flush=True)
            return

        if not self.last_6972_value:
            print(
                "BATTERY CONTROL blocked: missing current 6972 backup. Real write requires yuanzhi.",
                flush=True,
            )
            return

        token = self.login()

        if not token:
            print("BATTERY CONTROL blocked: no token", flush=True)
            return

        self._post("/v2/api/control", payload, token=token)

    def resume_discharge(self, mode="manual"):
        print(f"BATTERY CONTROL resume discharge requested mode={mode}", flush=True)

        if not self.last_6972_value:
            print(
                "BATTERY CONTROL restore skipped: no previous 6972 backup available",
                flush=True,
            )
            return

        payload = {
            "cid": str(self.cid_charge_discharge_one_cid),
            "inverterSn": self.inverter_sn,
            "value": self.last_6972_value,
            "yuanzhi": self.last_6972_value,
            "language": self.language,
        }

        if self.dry_run:
            print("BATTERY CONTROL DRY-RUN restore: no Solis command sent", flush=True)
            print("BATTERY CONTROL DRY-RUN restore payload:", payload, flush=True)
            return

        token = self.login()

        if not token:
            print("BATTERY CONTROL restore blocked: no token", flush=True)
            return

        self._post("/v2/api/control", payload, token=token)
