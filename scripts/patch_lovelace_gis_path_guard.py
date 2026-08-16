#!/usr/bin/env python3
"""Patch Acasă + Meteo cards: GIS iframe only when gis_map_path is set."""
from __future__ import annotations

import json
from pathlib import Path

NEEDLE_OLD = "html += mapGis(mapId, w.gis_map_path);"
NEEDLE_NEW = (
    "if (w.gis_map_path) {\n"
    "                html += mapGis(mapId, w.gis_map_path);\n"
    "              }"
)
# Live cards may use different indentation
VARIANTS = [
    (
        "html += mapGis(mapId, w.gis_map_path);",
        "if (w.gis_map_path) {\n        html += mapGis(mapId, w.gis_map_path);\n      }",
    ),
    (
        "html += mapGis(mapId, w.gis_map_path);",
        "if (w.gis_map_path) {\n              html += mapGis(mapId, w.gis_map_path);\n            }",
    ),
]


def patch_label(label: str) -> tuple[str, bool]:
    if "if (w.gis_map_path)" in label and "mapGis" in label:
        return label, False
    if NEEDLE_OLD not in label:
        return label, False
    # Prefer indentation matching surrounding block
    i = label.find(NEEDLE_OLD)
    # look at indent of previous line
    line_start = label.rfind("\n", 0, i) + 1
    indent = label[line_start:i]
    replacement = (
        f"if (w.gis_map_path) {{\n{indent}  html += mapGis(mapId, w.gis_map_path);\n{indent}}}"
    )
    return label[:i] + replacement + label[i + len(NEEDLE_OLD) :], True


def patch_file(path: Path) -> int:
    data = json.loads(path.read_text())
    patched = 0

    def walk(obj):
        nonlocal patched
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "label" and isinstance(v, str) and "mapGis" in v:
                    new_v, changed = patch_label(v)
                    if changed:
                        obj[k] = new_v
                        patched += 1
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    if patched:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return patched


def main() -> None:
    total = 0
    for name in ("lovelace.dashboard_acasa", "lovelace.dashboard_meteo"):
        p = Path("/config/.storage") / name
        if not p.exists():
            print(f"missing {name}")
            continue
        n = patch_file(p)
        print(f"{name}: patched={n}")
        total += n
    print(f"total={total}")


if __name__ == "__main__":
    main()
