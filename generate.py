#!/usr/bin/env python3
"""
Run this whenever you add or change photos.
It scans property folders and emits:
  - properties.json              (index of all properties + photos)
  - index.html                   (home page)
  - <slug>/index.html            (one static page per property)

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
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
OUTPUT_JSON = BASE_DIR / "properties.json"


def normalize(name: str) -> str:
    name = os.path.splitext(name)[0]
    name = re.sub(r"[-_ ]*[Ee]dit[-_ ]*", "", name)
    name = re.sub(r"[_\s]+$", "", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name.lower()


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "property"


def nice_label(raw: str) -> str:
    s = re.sub(r"[-_ ]*[Ee]dit.*$", "", raw).strip(" _-")
    s = re.sub(r"[-_]+", " ", s)
    return s.strip().title()


def rel_parts(folder_name: str, sub: str, file_name: str) -> str:
    return "/".join(urllib.parse.quote(p) for p in (folder_name, sub, file_name))


def collect_properties():
    props = []
    for folder in sorted(BASE_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name.startswith(".") or folder.name in SKIP_FOLDERS:
            continue
        raw_dir = folder / "Raw"
        edited_dir = folder / "Edited"
        if not raw_dir.exists() or not edited_dir.exists():
            continue

        raw_files = sorted(
            [f for f in raw_dir.iterdir() if f.suffix.lower() in EXTS],
            key=lambda x: x.name.lower(),
        )
        edited_files = sorted(
            [f for f in edited_dir.iterdir() if f.suffix.lower() in EXTS],
            key=lambda x: x.name.lower(),
        )
        raw_map = {normalize(f.name): f for f in raw_files}
        edited_map = {normalize(f.name): f for f in edited_files}

        photos = []
        for key in sorted(set(raw_map) | set(edited_map)):
            r = raw_map.get(key)
            e = edited_map.get(key)
            if not r and not e:
                continue
            photos.append({
                "label": nice_label((e or r).stem),
                "raw_path": rel_parts(folder.name, "Raw", r.name) if r else None,
                "edited_path": rel_parts(folder.name, "Edited", e.name) if e else None,
            })

        slug = slugify(folder.name)
        cover = (photos[0]["edited_path"] or photos[0]["raw_path"]) if photos else None
        props.append({
            "slug": slug,
            "name": folder.name,
            "cover_path": cover,
            "count": len(photos),
            "photos": photos,
        })
    return props


def with_prefix(props, prefix: str):
    out = []
    for p in props:
        photos = [{
            "label": ph["label"],
            "raw":    (prefix + ph["raw_path"])    if ph["raw_path"]    else None,
            "edited": (prefix + ph["edited_path"]) if ph["edited_path"] else None,
        } for ph in p["photos"]]
        out.append({
            "slug":  p["slug"],
            "name":  p["name"],
            "cover": (prefix + p["cover_path"]) if p["cover_path"] else None,
            "count": p["count"],
            "photos": photos,
        })
    return out


# Templates are loaded from sibling files kept in templates/ so this file stays readable.
TEMPLATES_DIR = BASE_DIR / "templates"


def _read(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def render_home(props_home):
    shell = _read("shell.html")
    home_css = _read("home.css")
    home_body = _read("home.html")
    data = json.dumps([
        {"slug": p["slug"], "name": p["name"], "cover": p["cover"], "count": p["count"]}
        for p in props_home
    ])
    return shell.replace("{{TITLE}}", "Real Estate Photo Editing — Portfolio, Matt Bloomfield") \
                .replace("{{EXTRA_CSS}}", home_css) \
                .replace("{{BODY}}", home_body) \
                .replace("{{DATA_SCRIPT}}", f"<script>window.__PROPS__ = {data};</script>")


def render_property(prop, all_props_for_nav):
    shell = _read("shell.html")
    prop_css = _read("property.css")
    prop_body = _read("property.html")
    prop_data = json.dumps(prop)
    all_data  = json.dumps([
        {"slug": p["slug"], "name": p["name"], "count": p["count"]}
        for p in all_props_for_nav
    ])
    return shell.replace("{{TITLE}}", f"{prop['name']} — Matt Bloomfield") \
                .replace("{{EXTRA_CSS}}", prop_css) \
                .replace("{{BODY}}", prop_body) \
                .replace("{{DATA_SCRIPT}}",
                         f"<script>window.__PROP__ = {prop_data}; window.__ALL__ = {all_data};</script>")


def main():
    props = collect_properties()
    if not props:
        print("  (no properties found)")
        return

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(with_prefix(props, "./"), f, indent=2, ensure_ascii=False)

    home_props = with_prefix(props, "./")
    (BASE_DIR / "index.html").write_text(render_home(home_props), encoding="utf-8")

    prop_props = with_prefix(props, "../")
    for p in prop_props:
        out_dir = BASE_DIR / p["slug"]
        out_dir.mkdir(exist_ok=True)
        (out_dir / "index.html").write_text(
            render_property(p, prop_props),
            encoding="utf-8"
        )

    total = sum(p["count"] for p in props)
    print(f"  Wrote properties.json  ({len(props)} properties, {total} photos)")
    print(f"  Wrote index.html       (home)")
    for p in prop_props:
        print(f"  Wrote {p['slug']}/index.html")


if __name__ == "__main__":
    main()
