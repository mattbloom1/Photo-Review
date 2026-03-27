#!/usr/bin/env python3
"""
Simple local server for the Photo Editing Showcase site.
Run: python3 server.py
Then open: http://localhost:8080
"""

import http.server
import json
import os
import re
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
PORT = 8080
SKIP_FOLDERS = {"Template"}


def normalize(name: str) -> str:
    """Strip extension, -Edit suffixes, trailing separators/spaces for matching."""
    name = os.path.splitext(name)[0]
    name = re.sub(r'[-_ ]*[Ee]dit[-_ ]*', '', name)
    name = re.sub(r'[_\s]+$', '', name).strip()
    name = re.sub(r'\s+', ' ', name)
    return name.lower()


def get_properties():
    properties = []
    for folder in sorted(BASE_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name.startswith('.') or folder.name in SKIP_FOLDERS:
            continue
        raw_dir = folder / 'Raw'
        edited_dir = folder / 'Edited'
        if not raw_dir.exists() or not edited_dir.exists():
            continue

        EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        raw_files = sorted([f for f in raw_dir.iterdir() if f.suffix.lower() in EXTS], key=lambda x: x.name.lower())
        edited_files = sorted([f for f in edited_dir.iterdir() if f.suffix.lower() in EXTS], key=lambda x: x.name.lower())

        # Build lookup: normalized_name -> path
        raw_map = {normalize(f.name): f for f in raw_files}
        edited_map = {normalize(f.name): f for f in edited_files}

        all_keys = sorted(set(raw_map) | set(edited_map))
        photos = []
        for key in all_keys:
            raw_f = raw_map.get(key)
            edited_f = edited_map.get(key)
            if not edited_f and not raw_f:
                continue
            label = (edited_f or raw_f).stem
            label = re.sub(r'[-_ ]*[Ee]dit.*$', '', label).strip(' _-')
            photos.append({
                "label": label,
                "raw": f"/images/{urllib.parse.quote(folder.name)}/Raw/{urllib.parse.quote((raw_f or edited_f).name)}" if raw_f else None,
                "edited": f"/images/{urllib.parse.quote(folder.name)}/Edited/{urllib.parse.quote((edited_f or raw_f).name)}" if edited_f else None,
            })

        cover = photos[0]["edited"] or photos[0]["raw"] if photos else None
        properties.append({
            "id": re.sub(r'[^a-z0-9]', '-', folder.name.lower()),
            "name": folder.name,
            "cover": cover,
            "count": len(photos),
            "photos": photos,
        })
    return properties


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logs

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/properties':
            data = json.dumps(get_properties()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)

        elif path.startswith('/images/'):
            rel = urllib.parse.unquote(path[len('/images/'):])
            file_path = BASE_DIR / rel
            if file_path.exists() and file_path.is_file():
                ext = file_path.suffix.lower()
                mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}.get(ext.lstrip('.'), 'application/octet-stream')
                with open(file_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', len(data))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)

        elif path == '/' or path == '/index.html':
            file_path = BASE_DIR / 'index.html'
            with open(file_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)

        else:
            self.send_error(404)


if __name__ == '__main__':
    server = http.server.HTTPServer(('', PORT), Handler)
    print(f'  ✦ Photo Showcase running at http://localhost:{PORT}')
    print(f'  Press Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.')
