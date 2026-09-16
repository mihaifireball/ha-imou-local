"""Bounded, read-only DVRIP probes; no arbitrary RPC or raw response export."""

import copy
import json
import struct
import threading
import time

from imou_ptz.dvrip import DahuaDVRIP


# Candidate names, NOT a claim of support by any particular camera firmware.
PROBES = (
    ("system.listService", {}),
    ("configManager.getConfig", {"name": "LeLensMask"}),
    ("configManager.getConfig", {"name": "LensMask"}),
    ("configManager.getConfig", {"name": "PrivacyMode"}),
)
MAX_RESPONSE = 65536
READ_SECONDS = 4.0
SAFE_SERVICES = frozenset({"system", "configManager", "lensMask", "leLensMask", "ptz"})
SAFE_FIELDS = frozenset({
    "Enable", "Enabled", "Status", "State", "Mode", "Support", "Supported",
    "MaskEnable", "PrivacyEnable", "LensMaskEnable",
})
SAFE_VALUES = frozenset({
    "on", "off", "open", "close", "closed", "true", "false", "auto",
    "enabled", "disabled", "normal", "privacy",
})


def safe_table(value, depth=0):
    """Only export known state fields. Unknown keys, strings, IDs are dropped."""
    if depth > 3:
        return None
    if isinstance(value, list):
        return [safe_table(item, depth + 1) for item in value[:8]]
    if not isinstance(value, dict):
        return None
    result = {}
    for key in sorted(SAFE_FIELDS & value.keys()):
        item = value[key]
        if isinstance(item, bool):
            result[key] = item
        elif type(item) is int and 0 <= item <= 16:
            result[key] = item
        elif isinstance(item, str) and item.lower() in SAFE_VALUES:
            result[key] = item.lower()
    return result


def summarize(method, reply):
    """Never include camera exception messages, raw payloads or identity fields."""
    result = reply.get("result")
    out = {"status": "accepted" if result is True else "rejected" if result is False else "unrecognized"}
    error = reply.get("error")
    if isinstance(error, dict) and type(error.get("code")) is int:
        out["error_code"] = error["code"]
    params = reply.get("params")
    if not isinstance(params, dict) or result is not True:
        return out
    if method == "system.listService":
        services = params.get("service")
        if isinstance(services, list):
            out["relevant_services"] = sorted(
                {s for s in services if isinstance(s, str) and s in SAFE_SERVICES}
            )
    elif "table" in params:
        out["safe_state_fields"] = safe_table(params["table"])
    return out


class ReadOnlyClient(DahuaDVRIP):
    def read_probe(self, method, params):
        # Guard the wire operation itself, not merely the HTTP route.
        if (method, params) not in PROBES:
            raise ValueError("Probe not allowed")
        request_id = self.cmd_id
        deadline = time.monotonic() + READ_SECONDS
        raw = bytearray(super()._send_json(method, params))

        def receive_until(size):
            while len(raw) < size:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                self.sock.settimeout(remaining)
                chunk = self.sock.recv(size - len(raw))
                if not chunk:
                    raise ConnectionError()
                raw.extend(chunk)

        receive_until(32)
        length = struct.unpack_from("<I", raw, 4)[0]
        if not 0 < length <= MAX_RESPONSE:
            raise ValueError("Invalid DVRIP length")
        receive_until(32 + length)
        reply = json.loads(bytes(raw[32:32 + length]).rstrip(b"\x00"))
        if not isinstance(reply, dict) or reply.get("id") != request_id:
            raise ValueError("Unexpected DVRIP response")
        return reply


class PrivacyDiagnostics:
    """One job per process, using its own socket; HTTP polling never reruns it."""

    def __init__(self, camera_config, client_factory=ReadOnlyClient):
        self._config = camera_config
        self._factory = client_factory
        self._lock = threading.Lock()
        self._report = {
            "diagnostic_version": 1,
            "read_only": True,
            "status": "not_started",
            "privacy_support": "not_determined",
            "checks": [],
            "note": "Candidate queries only. Accepted does not prove Privacy control or audio/video shutdown.",
        }

    def snapshot(self):
        with self._lock:
            if self._report["status"] == "not_started":
                self._report["status"] = "running"
                threading.Thread(target=self._run, daemon=True, name="privacy-diagnostic").start()
            return copy.deepcopy(self._report)

    def _run(self):
        cam = None
        try:
            c = self._config
            cam = self._factory(c["host"], c.get("dvrip_port", 37777), c["username"], c["password"])
            cam.connect()
            for method, params in PROBES:
                entry = {"method": method, "params": dict(params)}
                try:
                    entry.update(summarize(method, cam.read_probe(method, params)))
                except TimeoutError:
                    entry["status"] = "timeout"
                except (ValueError, UnicodeError, struct.error):
                    entry["status"] = "unrecognized_response"
                except Exception:
                    entry["status"] = "transport_error"
                with self._lock:
                    self._report["checks"].append(entry)
                # Never reuse a possibly desynchronized socket after a read failure.
                if entry["status"] in {"timeout", "unrecognized_response", "transport_error"}:
                    with self._lock:
                        self._report["status"] = "incomplete"
                    return
            with self._lock:
                self._report["status"] = "complete"
        except Exception:
            with self._lock:
                self._report["status"] = "connection_or_login_failed"
        finally:
            if cam is not None:
                cam.close()
