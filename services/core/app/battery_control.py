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

        self.auto_validate = (
            os.getenv("SOLIS_CONTROL_AUTO_VALIDATE", "true").lower()
            in ["1", "true", "yes", "on"]
        )

        self.read_spacing_s = float(os.getenv("SOLIS_CONTROL_READ_SPACING_S", "0.70"))
        self.last_read_time = 0.0

        self.token = None
        self.token_time = 0
        self.token_validity_s = 3600

        self.cid_new_earning_marker = 6798
        self.cid_charge_discharge_one_cid = 6972

        self.mode_cids = {
            636: "Storage Inverters Control Switching",
            100: "Time of Use Select",
            543: "Time of Use / Work mode candidate",
            109: "Allow Grid Charging",
        }

        self.marker_6798_value = None
        self.last_6972_value = None
        self.last_6972_backup_time = None
        self.active_6972_value = None

        self.validation_done = False
        self.last_validation_attempt = 0
        self.validation_retry_interval_s = 300

        self.last_mode_values = {}

        self.charge_switch_cids = [5916, 5917, 5918, 5919, 5920, 5921]
        self.discharge_switch_cids = [5922, 5923, 5924, 5925, 5926, 5927]

        self.charge_soc_cids = [5928, 5929, 5930, 5931, 5932, 5933]
        self.charge_time_cids = [5946, 5949, 5952, 5955, 5958, 5961]
        self.charge_voltage_cids = [5947, 5950, 5953, 5956, 5959, 5962]
        self.charge_current_cids = [5948, 5951, 5954, 5957, 5960, 5963]

        self.discharge_time_cids = [5964, 5968, 5972, 5976, 5980, 5987]
        self.discharge_soc_cids = [5965, 5969, 5973, 5977, 5981, 5984]
        self.discharge_voltage_cids = [5966, 5970, 5974, 5978, 5982, 5985]
        self.discharge_current_cids = [5967, 5971, 5975, 5979, 5983, 5986]

        print(
            f"BATTERY CONTROL initialized dry_run={self.dry_run} inverter_sn={self._safe(self.inverter_sn)}",
            flush=True,
        )

        if self.inverter_sn and self.auto_validate:
            self.validate_solis_charge_discharge_settings(force=False)

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

        if self.inverter_sn and self.auto_validate and not self.validation_done:
            self.validate_solis_charge_discharge_settings(force=False)

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

    def _extract_read_value(self, response):
        if not isinstance(response, dict):
            return None

        data = response.get("data")

        if isinstance(data, dict):
            for key in ["msg", "value", "result", "data"]:
                if key in data and data.get(key) is not None:
                    return str(data.get(key))

        for key in ["msg", "value", "result"]:
            if key in response and response.get(key) is not None:
                return str(response.get(key))

        return None

    def _is_error_value(self, value):
        if value is None:
            return True

        text = str(value).strip().lower()

        if text == "":
            return True

        error_keywords = [
            "communication error",
            "please refresh",
            "try again later",
            "data error",
            "datalogger returns data abnormally",
            "forbidden",
            "not found",
            "too many requests",
            "error",
            "failed",
        ]

        return any(keyword in text for keyword in error_keywords)

    def _throttle_read(self):
        now = time.time()
        elapsed = now - self.last_read_time

        if elapsed < self.read_spacing_s:
            time.sleep(self.read_spacing_s - elapsed)

        self.last_read_time = time.time()

    def _looks_like_time_slot(self, value):
        if value is None:
            return False

        text = str(value).strip()

        if "-" in text:
            parts = text.split("-")
        elif "~" in text:
            parts = text.split("~")
        else:
            return False

        return len(parts) == 2 and ":" in parts[0] and ":" in parts[1]

    def _normalize_time_slot(self, value):
        if value is None:
            return "00:00-00:00"

        text = str(value).strip()
        text = text.replace("~", "-")
        text = text.replace(" ", "")

        if not self._looks_like_time_slot(text):
            return "00:00-00:00"

        return text

    def _normalize_switch(self, value):
        text = str(value).strip()

        if text in ["0", "off", "OFF", "false", "False"]:
            return "0"

        if text in ["1", "on", "ON", "true", "True"]:
            return "1"

        return "0"

    def _normalize_numeric(self, value, default_value):
        if value is None:
            return str(default_value)

        text = str(value).strip()

        if text == "":
            return str(default_value)

        if self._is_error_value(text):
            return str(default_value)

        return text

    def _looks_like_6972_value(self, value):
        if self._is_error_value(value):
            return False

        parts = [p.strip() for p in str(value).split(",")]

        if len(parts) != 60:
            print(
                f"BATTERY CONTROL CID 6972 invalid field count: {len(parts)} expected 60",
                flush=True,
            )
            return False

        for group_index in range(12):
            base = group_index * 5
            switch_value = parts[base]
            time_slot = parts[base + 1]

            if switch_value not in ["0", "1"]:
                print(
                    f"BATTERY CONTROL CID 6972 invalid switch in group {group_index + 1}: {switch_value}",
                    flush=True,
                )
                return False

            if not self._looks_like_time_slot(time_slot):
                print(
                    f"BATTERY CONTROL CID 6972 invalid time slot in group {group_index + 1}: {time_slot}",
                    flush=True,
                )
                return False

        return True

    def read_cid_once(self, cid):
        if not self.inverter_sn:
            print(f"BATTERY CONTROL read CID {cid} skipped: missing inverter SN", flush=True)
            return None

        self._throttle_read()

        payload = {
            "inverterSn": self.inverter_sn,
            "cid": int(cid),
        }

        response = self._post("/v2/api/atRead", payload)

        value = self._extract_read_value(response)

        if self._is_error_value(value):
            print(f"BATTERY CONTROL read CID {cid} returned invalid/error value: {value}", flush=True)
            return None

        print(f"BATTERY CONTROL read CID {cid} = {value}", flush=True)

        return value

    def read_cid(self, cid, attempts=2, delay_s=1):
        last_value = None

        for attempt in range(1, attempts + 1):
            print(
                f"BATTERY CONTROL read CID {cid} attempt {attempt}/{attempts}",
                flush=True,
            )

            value = self.read_cid_once(cid)

            if value is not None:
                return value

            last_value = value

            if attempt < attempts:
                time.sleep(delay_s)

        print(
            f"BATTERY CONTROL read CID {cid} failed after {attempts} attempts. Last value={last_value}",
            flush=True,
        )

        return None

    def validate_modes(self):
        print("BATTERY CONTROL mode validation started", flush=True)

        if not self.inverter_sn:
            print("BATTERY CONTROL mode validation skipped: missing inverter SN", flush=True)
            return False

        values = {}

        for cid, description in self.mode_cids.items():
            value = self.read_cid(cid, attempts=3, delay_s=2)
            values[str(cid)] = value

            if value is None:
                print(
                    f"BATTERY CONTROL mode CID {cid} ({description}) = UNREADABLE",
                    flush=True,
                )
            else:
                print(
                    f"BATTERY CONTROL mode CID {cid} ({description}) = {value}",
                    flush=True,
                )

        self.last_mode_values = values

        print("BATTERY CONTROL mode validation summary:", values, flush=True)

        return True

    def validate_solis_charge_discharge_settings(self, force=False):
        now = time.time()

        if not force:
            if now - self.last_validation_attempt < self.validation_retry_interval_s:
                return self.validation_done

        self.last_validation_attempt = now

        if not self.inverter_sn:
            print("BATTERY CONTROL validation skipped: missing inverter SN", flush=True)
            return False

        print("BATTERY CONTROL validation started", flush=True)

        marker = self.read_cid(self.cid_new_earning_marker, attempts=2, delay_s=1)

        if marker is not None:
            self.marker_6798_value = marker
            print(f"BATTERY CONTROL CID 6798 marker value: {marker}", flush=True)

            marker_normalized = str(marker).strip().lower()

            if marker_normalized in ["0xaa55", "aa55", "43605"]:
                print(
                    "BATTERY CONTROL new optimized earning parameters detected",
                    flush=True,
                )
            else:
                print(
                    "BATTERY CONTROL warning: CID 6798 is not 0xAA55. CID 6972/fallback may not match this firmware.",
                    flush=True,
                )
        else:
            print(
                "BATTERY CONTROL warning: unable to read CID 6798 marker",
                flush=True,
            )

        value_6972 = self.read_cid(
            self.cid_charge_discharge_one_cid,
            attempts=3,
            delay_s=2,
        )

        if value_6972 and self._looks_like_6972_value(value_6972):
            print("BATTERY CONTROL CID 6972 direct read OK", flush=True)
            self.set_current_6972_value(value_6972)
            self.validation_done = True
            self.print_validation_summary(value_6972)
            return True

        print(
            "BATTERY CONTROL CID 6972 direct read unavailable, trying unit CID fallback",
            flush=True,
        )

        fallback_value = self.read_6972_value_from_unit_cids()

        if not fallback_value:
            print(
                "BATTERY CONTROL validation failed: unable to rebuild CID 6972 from unit CIDs",
                flush=True,
            )
            self.validation_done = False
            return False

        if not self._looks_like_6972_value(fallback_value):
            print(
                "BATTERY CONTROL validation failed: rebuilt CID 6972 value is invalid",
                flush=True,
            )
            self.validation_done = False
            return False

        self.set_current_6972_value(fallback_value)
        self.validation_done = True

        print(
            "BATTERY CONTROL validation OK: CID 6972 rebuilt from unit CIDs",
            flush=True,
        )

        self.print_validation_summary(fallback_value)

        return True

    def print_validation_summary(self, value_6972):
        groups = self.split_6972_groups(value_6972)
        inhibit_value = self.build_inhibit_6972_value(value_6972)

        print(
            f"BATTERY CONTROL CID 6972 groups detected: {len(groups)}",
            flush=True,
        )

        print("BATTERY CONTROL 6972 current groups:", flush=True)

        for index, group in enumerate(groups):
            kind = "charge" if index < 6 else "discharge"
            print(
                f"BATTERY CONTROL group {index + 1:02d} {kind}: switch={group[0]} time={group[1]} current={group[2]} soc={group[3]} volt={group[4]}",
                flush=True,
            )

        print(f"BATTERY CONTROL current yuanzhi: {value_6972}", flush=True)
        print(f"BATTERY CONTROL dry-run inhibit value: {inhibit_value}", flush=True)

    def read_slot_value(self, cid, name, required=True):
        value = self.read_cid(cid, attempts=2, delay_s=1)

        if value is None:
            if required:
                print(
                    f"BATTERY CONTROL unit CID missing: {name} cid={cid}",
                    flush=True,
                )
            return None

        return value

    def read_6972_value_from_unit_cids(self):
        print("BATTERY CONTROL fallback unit CID read started", flush=True)

        groups = []

        for idx in range(6):
            switch_value = self.read_slot_value(
                self.charge_switch_cids[idx],
                f"charge switch {idx + 1}",
            )
            time_slot = self.read_slot_value(
                self.charge_time_cids[idx],
                f"charge time {idx + 1}",
            )
            current = self.read_slot_value(
                self.charge_current_cids[idx],
                f"charge current {idx + 1}",
            )
            soc = self.read_slot_value(
                self.charge_soc_cids[idx],
                f"charge soc {idx + 1}",
            )
            voltage = self.read_slot_value(
                self.charge_voltage_cids[idx],
                f"charge voltage {idx + 1}",
            )

            if None in [switch_value, time_slot, current, soc, voltage]:
                print(
                    f"BATTERY CONTROL fallback failed on charge group {idx + 1}",
                    flush=True,
                )
                return None

            groups.append([
                self._normalize_switch(switch_value),
                self._normalize_time_slot(time_slot),
                self._normalize_numeric(current, "0"),
                self._normalize_numeric(soc, "20"),
                self._normalize_numeric(voltage, "48"),
            ])

        for idx in range(6):
            switch_value = self.read_slot_value(
                self.discharge_switch_cids[idx],
                f"discharge switch {idx + 1}",
            )
            time_slot = self.read_slot_value(
                self.discharge_time_cids[idx],
                f"discharge time {idx + 1}",
            )
            current = self.read_slot_value(
                self.discharge_current_cids[idx],
                f"discharge current {idx + 1}",
            )
            soc = self.read_slot_value(
                self.discharge_soc_cids[idx],
                f"discharge soc {idx + 1}",
            )
            voltage = self.read_slot_value(
                self.discharge_voltage_cids[idx],
                f"discharge voltage {idx + 1}",
            )

            if None in [switch_value, time_slot, current, soc, voltage]:
                print(
                    f"BATTERY CONTROL fallback failed on discharge group {idx + 1}",
                    flush=True,
                )
                return None

            groups.append([
                self._normalize_switch(switch_value),
                self._normalize_time_slot(time_slot),
                self._normalize_numeric(current, "0"),
                self._normalize_numeric(soc, "20"),
                self._normalize_numeric(voltage, "48"),
            ])

        if len(groups) != 12:
            print(
                f"BATTERY CONTROL fallback invalid group count: {len(groups)}",
                flush=True,
            )
            return None

        rebuilt_value = self.join_6972_groups(groups)

        print(
            f"BATTERY CONTROL fallback rebuilt 6972 value: {rebuilt_value}",
            flush=True,
        )

        return rebuilt_value

    def set_current_6972_value(self, value):
        if not value:
            return

        if not self._looks_like_6972_value(value):
            print(
                "BATTERY CONTROL 6972 backup rejected: invalid value",
                flush=True,
            )
            return

        self.last_6972_value = str(value)
        self.last_6972_backup_time = time.time()

        print("BATTERY CONTROL 6972 backup updated", flush=True)

    def split_6972_groups(self, value):
        if not value:
            return []

        parts = [p.strip() for p in str(value).split(",")]

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

    def build_inhibit_6972_value(self, current_value):
        if not self._looks_like_6972_value(current_value):
            print(
                "BATTERY CONTROL cannot build inhibit value: invalid current CID 6972 value",
                flush=True,
            )
            return None

        groups = self.split_6972_groups(current_value)

        if len(groups) != 12:
            print(
                f"BATTERY CONTROL cannot safely build inhibit value: 6972 has {len(groups)} groups, expected 12",
                flush=True,
            )
            return None

        new_groups = []

        for index, group in enumerate(groups):
            new_group = list(group)

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

        if action == "validate_6972":
            self.validate_solis_charge_discharge_settings(force=True)
            return

        if action == "validate_modes":
            self.validate_modes()
            return

        if action == "arm_inhibit_discharge":
            print("BATTERY CONTROL armed for off-peak window", flush=True)

            if self.auto_validate and not self.validation_done:
                self.validate_solis_charge_discharge_settings(force=False)

            return

        if action == "inhibit_discharge":
            self.inhibit_discharge(mode=mode, duration_h=duration_h)
            return

        if action == "resume_discharge":
            self.resume_discharge(mode=mode)
            return

        if enabled is True:
            self.inhibit_discharge(mode=mode, duration_h=duration_h)
            return

        if enabled is False:
            self.resume_discharge(mode=mode)
            return

        print("BATTERY CONTROL unsupported command:", command, flush=True)

    def inhibit_discharge(self, mode="manual", duration_h=None):
        print(
            f"BATTERY CONTROL inhibit discharge requested mode={mode} duration_h={duration_h}",
            flush=True,
        )

        if not self.validation_done:
            self.validate_solis_charge_discharge_settings(force=True)

        if not self.last_6972_value:
            print(
                "BATTERY CONTROL inhibit blocked: no valid CID 6972 backup available",
                flush=True,
            )
            return

        new_value = self.build_inhibit_6972_value(self.last_6972_value)

        if not new_value:
            print(
                "BATTERY CONTROL inhibit blocked: unable to build safe CID 6972 value",
                flush=True,
            )
            return

        payload = {
            "cid": str(self.cid_charge_discharge_one_cid),
            "inverterSn": self.inverter_sn,
            "value": new_value,
            "yuanzhi": self.last_6972_value,
            "language": self.language,
        }

        if self.dry_run:
            print("BATTERY CONTROL DRY-RUN: no Solis command sent", flush=True)
            print("BATTERY CONTROL DRY-RUN payload:", payload, flush=True)
            return

        if not self.inverter_sn:
            print("BATTERY CONTROL blocked: missing inverter SN", flush=True)
            return

        token = self.login()

        if not token:
            print("BATTERY CONTROL blocked: no token", flush=True)
            return

        response = self._post("/v2/api/control", payload, token=token)

        print("BATTERY CONTROL inhibit response:", response, flush=True)

        self.active_6972_value = new_value

    def resume_discharge(self, mode="manual"):
        print(f"BATTERY CONTROL resume discharge requested mode={mode}", flush=True)

        if not self.last_6972_value:
            print(
                "BATTERY CONTROL restore skipped: no valid CID 6972 backup available",
                flush=True,
            )
            return

        current_yuanzhi = self.active_6972_value or self.last_6972_value

        payload = {
            "cid": str(self.cid_charge_discharge_one_cid),
            "inverterSn": self.inverter_sn,
            "value": self.last_6972_value,
            "yuanzhi": current_yuanzhi,
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

        response = self._post("/v2/api/control", payload, token=token)

        print("BATTERY CONTROL restore response:", response, flush=True)

        self.active_6972_value = None
