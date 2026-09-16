"""Keep the upstream PTZ/ONVIF handler and add a read-only diagnostic route."""

import os
from urllib.parse import urlsplit

from imou_ptz import server
from imou_ptz.handler import RequestHandler
from privacy_diagnostics import PrivacyDiagnostics


def make_handler(diagnostics):
    class DiagnosticHandler(RequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path.rstrip("/") == "/diagnostics/privacy":
                if url.query:
                    self._send_json({"error": "This endpoint does not accept query parameters"}, 400)
                    return
                self._send_json(diagnostics.snapshot())
                return
            super().do_GET()

        def do_POST(self):
            if urlsplit(self.path).path.rstrip("/") == "/diagnostics/privacy":
                self._send_json({"error": "Use GET; diagnostic writes are not supported"}, 405)
                return
            super().do_POST()

        def end_headers(self):
            if urlsplit(self.path).path.rstrip("/") == "/diagnostics/privacy":
                self.send_header("Cache-Control", "no-store")
            super().end_headers()

    return DiagnosticHandler


def main():
    config = {
        "host": os.environ["CAMERA_HOST"],
        "dvrip_port": int(os.environ.get("CAMERA_DVRIP_PORT", "37777")),
        "username": os.environ.get("CAMERA_USER", "admin"),
        "password": os.environ["CAMERA_PASSWORD"],
    }
    # Keep upstream's single-threaded HTTP server and PTZ serialization intact.
    # Only the diagnostic runs in a worker, on a separate camera session.
    server.RequestHandler = make_handler(PrivacyDiagnostics(config))
    print("[imou-ptz] Read-only diagnostic: GET /diagnostics/privacy", flush=True)
    server.run_server("0.0.0.0", 8000, config)


if __name__ == "__main__":
    main()
