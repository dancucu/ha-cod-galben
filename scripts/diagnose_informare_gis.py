#!/usr/bin/env python3
"""Diagnose ANM informare GIS availability."""
from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET

xml = urllib.request.urlopen(
    "https://www.meteoromania.ro/avertizari-xml.php",
    timeout=30,
).read().decode("utf-8", "replace")
root = ET.fromstring(xml)
print("count", len(root.findall("avertizare")))
for av in root.findall("avertizare"):
    tip = " | ".join(
        [
            av.get("tipMesaj") or "",
            av.get("numeTip") or "",
            av.get("numeCuloare") or "",
        ]
    )
    judete = list(av.findall("judet"))
    with_gis = sum(1 for j in judete if (j.get("coordGis") or "").strip())
    colors: dict[str, int] = {}
    for j in judete:
        key = j.get("culoare") or "?"
        colors[key] = colors.get(key, 0) + 1
    mesaj = av.get("mesaj") or ""
    m = re.search(r"MESAJ\s+(\d+)\s*/\s*(\d+)", mesaj, re.I)
    print("tip=", tip)
    print(
        "  judete=",
        len(judete),
        "coordGis=",
        with_gis,
        "colors=",
        colors,
        "mesaj=",
        m.groups() if m else None,
        "zona=",
        (av.get("zonaAfectata") or "")[:60],
    )

html = urllib.request.urlopen(
    "https://www.meteoromania.ro/avertizari/", timeout=30
).read().decode("utf-8", "replace")
ids: list[str] = []
seen: set[str] = set()
for mid in re.findall(r"id_avertizare=(\d+)", html):
    if mid not in seen:
        seen.add(mid)
        ids.append(mid)
print("map_ids", ids)

for mid in ids[:5]:
    url = (
        "https://www.meteoromania.ro/wp-content/plugins/meteo/harti/"
        f"harta.svg.php?id_avertizare={mid}"
    )
    try:
        data = urllib.request.urlopen(url, timeout=25).read()
        text = data.decode("utf-8", "replace")
        vb = re.search(r'viewBox="([^"]+)"', text)
        judet_paths = len(re.findall(r"\bjudet\b", text))
        cod0 = len(re.findall(r"\bcod0\b", text))
        print(
            "svg",
            mid,
            "bytes",
            len(data),
            "viewBox",
            vb.group(1) if vb else None,
            "judet_cls",
            judet_paths,
            "cod0",
            cod0,
        )
    except Exception as err:
        print("svg", mid, err)
