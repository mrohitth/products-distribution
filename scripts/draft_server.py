#!/usr/bin/env python3
"""
Lightweight file server for product drafts.
Serves /products/drafts/ directory on localhost:8765
Links expire after 14 days (files older than 14 days return 410 Gone)
"""
import http.server
import os
from pathlib import Path
from datetime import datetime, timedelta

DRAFTS_DIR = Path("/home/mathew/.openclaw/workspace/products/drafts")
PORT = 8765
MAX_AGE_DAYS = 14

class DraftHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DRAFTS_DIR), **kwargs)

    def do_GET(self):
        path = self.translate_path(self.path)
        if os.path.isfile(path):
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if datetime.now() - mtime > timedelta(days=MAX_AGE_DAYS):
                self.send_error(410, "Link expired (>14 days)")
                return
        super().do_GET()

if __name__ == "__main__":
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(str(DRAFTS_DIR))
    server = http.server.HTTPServer(("127.0.0.1", PORT), DraftHandler)
    print(f"Serving drafts on http://127.0.0.1:{PORT}")
    server.serve_forever()
