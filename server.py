#!/usr/bin/env python3
"""
Simple local static file server for the portfolio site.
After running `python generate.py`, run this to preview locally.

Usage:
    python3 server.py
Then open: http://localhost:8080
"""

import http.server
import os
import socketserver
from pathlib import Path

BASE_DIR = Path(__file__).parent
PORT = 8080


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"  Portfolio site running at http://localhost:{PORT}")
        print(f"  Serving from: {BASE_DIR}")
        print(f"  Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")
