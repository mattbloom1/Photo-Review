#!/usr/bin/env python3
"""
Run this script once (locally) whenever you add or change photos.
It scans your property folders and writes properties.json,
which index.html uses when hosted on GitHub Pages.

Usage:
    python3 generate.py
"""

import json
import os
import re
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
SKIP_FOLDERS = {"Template", "Unsure"}
OUTPUT_FILE = BASE_DIR / "properties.json"


def normalize(name: str) -> str:
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
        raw_files = sorted(
            [f for f in raw_dir.iterdir() if f.suffix.lower() in EXTS],
            key=lambda x: x.name.lower()
        )
        edited_files = sorted(
            [f for f in edited_dir.iterdir() if f.suffix.lower() in EXTS],
            key=lambda x: x.name.lower()
        )

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

            def rel_url(f):
                # Relative URL from repo root — works on GitHub Pages
                parts = [urllib.parse.quote(folder.name),
                         urllib.parse.quote(f.parent.name),
                         urllib.parse.quote(f.name)]
                return './' + '/'.join(parts)

            photos.append({
                "label": label,
                "raw":    rel_url(raw_f)    if raw_f    else None,
                "edited": rel_url(edited_f) if edited_f else None,
            })

        cover = photos[0]["edited"] or photos[0]["raw"] if photos else None
        properties.append({
            "id":     re.sub(r'[^a-z0-9]', '-', folder.name.lower()),
            "name":   folder.name,
            "cover":  cover,
            "count":  len(photos),
            "photos": photos,
        })
    return properties


if __name__ == '__main__':
    props = get_properties()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(props, f, indent=2, ensure_ascii=False)
    total_photos = sum(p['count'] for p in props)
    print(f'✦ Written {OUTPUT_FILE.name}')
    print(f'  {len(props)} properties · {total_photos} photos')
