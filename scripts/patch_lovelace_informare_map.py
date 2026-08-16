#!/usr/bin/env python3
"""Remove informare map skip on lovelace.dashboard_acasa AVERTIZARE METEO card."""
from __future__ import annotations

import json
from pathlib import Path

STORAGE = Path("/config/.storage/lovelace.dashboard_acasa")

OLD = "if (mapId && (w.level || '').toLowerCase() !== 'informare')"
OLD_DQ = 'if (mapId && (w.level || "").toLowerCase() !== "informare")'
NEW = "if (mapId)"


def patch_label(label: str) -> tuple[str, bool]:
    if OLD in label:
        return label.replace(OLD, NEW), True
    if OLD_DQ in label:
        return label.replace(OLD_DQ, NEW), True
    # Already patched or different wording
    if "mapImg" in label and "!== 'informare'" not in label and '!== "informare"' not in label:
        return label, False
    return label, False


def main() -> None:
    data = json.loads(STORAGE.read_text())
    patched = 0
    already = 0

    def walk(obj):
        nonlocal patched, already
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "label" and isinstance(v, str) and "mapImg" in v and "resolveMapId" in v:
                    new_v, changed = patch_label(v)
                    if changed:
                        obj[k] = new_v
                        patched += 1
                    elif "if (mapId)" in v and "informare" not in v[v.find("if (mapId") : v.find("if (mapId") + 80]:
                        already += 1
                    else:
                        # show snippet for debug
                        i = v.find("if (mapId")
                        print("unpatched snippet:", repr(v[i : i + 120]) if i >= 0 else "no if (mapId)")
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    if patched:
        STORAGE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"patched={patched} already_ok={already}")


if __name__ == "__main__":
    main()
