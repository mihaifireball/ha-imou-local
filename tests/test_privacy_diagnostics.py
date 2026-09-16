"""Run with upstream on PYTHONPATH: python3 -m unittest discover -s tests -v."""

import http.client
import json
from pathlib import Path
import struct
import sys
import threading
import time
import unittest
from http.server import HTTPServer
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "imou-ptz"))
from privacy_diagnostics import PROBES, PrivacyDiagnostics, ReadOnlyClient, safe_table, summarize
from proxy import make_handler


CONFIG = {"host": "127.0.0.1", "username": "admin", "password": "SECRET"}


def frame(reply):
    payload = json.dumps(reply).encode()
    return struct.pack("<II", 0xF7, len(payload)) + bytes(24) + payload


class FakeSocket:
    def __init__(self, data, chunk_size=7):
        self.data = data
        self.chunk_size = chunk_size
        self.sent = []

    def settimeout(self, value):
        pass

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        n = min(size, self.chunk_size)
        result, self.data = self.data[:n], self.data[n:]
        return result


class ProbeClient:
    instances = []

    def __init__(self, *args):
        self.calls = []
        self.closed = False
        self.instances.append(self)

    def connect(self):
        pass

    def close(self):
        self.closed = True

    def read_probe(self, method, params):
        self.calls.append((method, params))
        return {"result": True, "params": {"table": {"Enable": False, "Password": "SECRET"}}}


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        ProbeClient.instances = []

    def completed(self, diag):
        for _ in range(100):
            result = diag.snapshot()
            if result["status"] != "running":
                return result
            time.sleep(0.005)
        self.fail("Diagnostic worker did not complete")

    def test_filter_sensitive_fields_and_strings(self):
        result = safe_table({"Enable": True, "Password": "SECRET", "SerialNo": "SERIAL", "Mode": "SECRET", "State": "On", "Status": 2})
        self.assertEqual(result, {"Enable": True, "State": "on", "Status": 2})
        self.assertEqual(safe_table([{"Enable": False}, {"Token": "SECRET"}]), [{"Enable": False}, {}])
        self.assertIsNone(safe_table("SECRET"))

    def test_filter_service_names(self):
        result = summarize("system.listService", {"result": True, "params": {"service": ["ptz", "SECRET", {}, "lensMask"]}, "session": "SECRET"})
        self.assertEqual(result["relevant_services"], ["lensMask", "ptz"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_error_message_not_exported(self):
        result = summarize("configManager.getConfig", {"result": False, "error": {"code": 123, "message": "password SECRET"}})
        self.assertEqual(result, {"status": "rejected", "error_code": 123})

    def test_unknown_reply_is_not_success(self):
        self.assertEqual(summarize("configManager.getConfig", {})["status"], "unrecognized")

    def test_one_run_only_and_session_closed(self):
        diag = PrivacyDiagnostics(CONFIG, ProbeClient)
        result = self.completed(diag)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["privacy_support"], "not_determined")
        self.assertEqual(len(result["checks"]), len(PROBES))
        result["checks"].clear()
        self.assertEqual(len(diag.snapshot()["checks"]), len(PROBES))
        self.assertEqual(len(ProbeClient.instances), 1)
        self.assertEqual(ProbeClient.instances[0].calls, list(PROBES))
        self.assertTrue(ProbeClient.instances[0].closed)
        self.assertNotIn("SECRET", json.dumps(diag.snapshot()))

    def test_failed_login_closes_and_does_not_probe(self):
        class FailedClient(ProbeClient):
            def connect(self):
                raise RuntimeError("SECRET")
        diag = PrivacyDiagnostics(CONFIG, FailedClient)
        result = self.completed(diag)
        self.assertEqual(result["status"], "connection_or_login_failed")
        self.assertEqual(ProbeClient.instances[0].calls, [])
        self.assertTrue(ProbeClient.instances[0].closed)
        self.assertNotIn("SECRET", json.dumps(result))

    def test_timeout_stops_remaining_probes(self):
        class TimeoutClient(ProbeClient):
            def read_probe(self, method, params):
                raise TimeoutError("SECRET")
        result = self.completed(PrivacyDiagnostics(CONFIG, TimeoutClient))
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(len(result["checks"]), 1)
        self.assertEqual(result["checks"][0]["status"], "timeout")

    def test_invalid_reply_stops_remaining_probes(self):
        class InvalidClient(ProbeClient):
            def read_probe(self, method, params):
                raise ValueError("SECRET")
        result = self.completed(PrivacyDiagnostics(CONFIG, InvalidClient))
        self.assertEqual(result["checks"][0]["status"], "unrecognized_response")
        self.assertEqual(result["status"], "incomplete")

    def client_with(self, data):
        cam = ReadOnlyClient("unused")
        cam.sock = FakeSocket(data)
        return cam

    def test_fragmented_frame_and_read_request(self):
        cam = self.client_with(frame({"id": 1, "result": True}))
        reply = cam.read_probe("system.listService", {})
        self.assertTrue(reply["result"])
        request = json.loads(cam.sock.sent[0][32:])
        self.assertEqual(request["method"], "system.listService")

    def test_disallowed_methods_and_names_never_sent(self):
        cam = self.client_with(b"")
        for method, params in [("configManager.setConfig", {}), ("configManager.getConfig", {"name": "All"}), ("ptz.start", {}), ("system.reboot", {})]:
            with self.assertRaises(ValueError):
                cam.read_probe(method, params)
        self.assertEqual(cam.sock.sent, [])

    def test_response_id_mismatch(self):
        cam = self.client_with(frame({"id": 99, "result": True}))
        with self.assertRaises(ValueError):
            cam.read_probe("system.listService", {})

    def test_oversized_and_empty_frame(self):
        for length in [0, 65537]:
            cam = self.client_with(struct.pack("<II", 0xF7, length) + bytes(24))
            with self.assertRaises(ValueError):
                cam.read_probe("system.listService", {})

    def test_eof(self):
        cam = self.client_with(b"short")
        with self.assertRaises(ConnectionError):
            cam.read_probe("system.listService", {})

    def test_deadline(self):
        cam = self.client_with(b"short")
        with patch("privacy_diagnostics.time.monotonic", side_effect=[0, 5]):
            with self.assertRaises(TimeoutError):
                cam.read_probe("system.listService", {})

    def test_http_diagnostic_health_and_ptz(self):
        gate = threading.Event()

        class SlowClient(ProbeClient):
            def connect(self):
                gate.wait(2)

        class Ptz:
            def __init__(self):
                self.moves = []

            def ptz_move(self, code, speed, duration):
                self.moves.append((code, speed, duration))

        diag = PrivacyDiagnostics(CONFIG, SlowClient)
        handler = make_handler(diag)
        ptz = handler.dvrip = Ptz()
        httpd = HTTPServer(("127.0.0.1", 0), handler)
        worker = threading.Thread(target=httpd.serve_forever, daemon=True)
        worker.start()
        conn = http.client.HTTPConnection("127.0.0.1", httpd.server_port, timeout=1)

        def request(method, path):
            conn.request(method, path)
            response = conn.getresponse()
            return response.status, response.getheader("Cache-Control"), json.loads(response.read())

        try:
            code, cache, body = request("GET", "/diagnostics/privacy")
            self.assertEqual((code, cache, body["status"]), (200, "no-store", "running"))
            self.assertEqual(request("GET", "/health")[0], 200)
            self.assertEqual(request("GET", "/ptz/move?code=Right&speed=2&duration=0.4")[0], 200)
            self.assertEqual(ptz.moves, [("Right", 2, 0.4)])
            self.assertEqual(request("GET", "/diagnostics/privacy?method=system.reboot")[0], 400)
            self.assertEqual(request("POST", "/diagnostics/privacy")[0], 405)
            conn.request("POST", "/onvif/device_service", body=(
                '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
                'xmlns:tds="http://www.onvif.org/ver10/device/wsdl">'
                '<s:Body><tds:GetSystemDateAndTime/></s:Body></s:Envelope>'
            ), headers={"Content-Type": "application/soap+xml"})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn(b"GetSystemDateAndTimeResponse", response.read())
            gate.set()
            self.completed(diag)
            self.assertEqual(request("GET", "/diagnostics/privacy")[2]["status"], "complete")
        finally:
            gate.set()
            conn.close()
            httpd.shutdown()
            httpd.server_close()
            worker.join(2)


if __name__ == "__main__":
    unittest.main()
