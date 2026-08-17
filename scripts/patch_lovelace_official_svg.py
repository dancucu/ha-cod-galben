#!/usr/bin/env python3
"""Point official ANM maps at local harta_anm SVG with cache-bust."""
from __future__ import annotations

import json
from pathlib import Path

NEW_MAPIMG = """const mapImg = (id, path) => {
            if (!id || !showOficial) return '';
            const local = `${(path || `/local/cod_galben/harta_anm_${id}.svg`).split('?')[0]}?v=1.3.7`;
            const legacy = `/local/harta_anm_${id}.svg?v=1.3.7`;
            return `<div style="text-align:center;margin-top:10px;margin-bottom:6px;">
              <div style="font-size:11px;opacity:0.7;margin-bottom:4px;">Hartă oficială ANM</div>
              <img src="${local}"
                   onerror="if(!this.dataset.fb){this.dataset.fb=1;this.src='${legacy}';}else{this.onerror=null;}"
                   alt="Hartă oficială ANM"
                   style="width:100%;max-width:480px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.25);" />
            </div>`;
          };"""

NEW_MAPIMG_COMPACT = """const mapImg = (id, path) => {
      if (!id || !showOficial) return '';
      const local = `${(path || `/local/cod_galben/harta_anm_${id}.svg`).split('?')[0]}?v=1.3.7`;
      const legacy = `/local/harta_anm_${id}.svg?v=1.3.7`;
      return `<div style="text-align:center;margin-top:10px;margin-bottom:6px;">
              <div style="font-size:11px;opacity:0.7;margin-bottom:4px;">Hartă oficială ANM</div>
              <img src="${local}"
                   onerror="if(!this.dataset.fb){this.dataset.fb=1;this.src='${legacy}';}else{this.onerror=null;}"
                   alt="Hartă oficială ANM"
                   style="width:100%;max-width:480px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.25);" />
            </div>`;
          };"""


def _replace_mapimg(label: str) -> str:
    start = label.find("const mapImg = (id")
    if start < 0:
        return label
    end = label.find("const mapGis", start)
    if end < 0:
        return label
    indent_nl = label.rfind("\n", 0, start)
    compact = indent_nl >= 0 and (start - indent_nl) <= 8
    replacement = NEW_MAPIMG_COMPACT if compact else NEW_MAPIMG
    return label[:start] + replacement + "\n\n          " + label[end:]


def _replace_call(label: str) -> str:
    if "mapImg(mapId, w.official_map_path)" in label:
        return label
    return label.replace(
        "html += mapImg(mapId);", "html += mapImg(mapId, w.official_map_path);"
    )


def patch_label(label: str) -> tuple[str, bool]:
    new = _replace_call(_replace_mapimg(label))
    return new, new != label


def patch_file(path: Path) -> int:
    data = json.loads(path.read_text())
    patched = 0

    def walk(obj):
        nonlocal patched
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "label" and isinstance(v, str) and "mapImg" in v:
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
    for name in ("lovelace.dashboard_acasa", "lovelace.dashboard_meteo"):
        p = Path("/config/.storage") / name
        if not p.exists():
            print(f"missing {name}")
            continue
        print(f"{name}: patched={patch_file(p)}")


if __name__ == "__main__":
    main()
