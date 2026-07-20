#!/usr/bin/env python3
"""Patch lovelace.dashboard_meteo to show Mesaj N/M in warning titles."""
import json
from pathlib import Path

STORAGE = Path("/config/.storage/lovelace.dashboard_meteo")

MESAJ_LABEL_FN = """
          const mesajLabel = (w, index, total) => {
            let nr = w.mesaj_nr;
            let tot = w.mesaj_total;
            if (!nr || !tot) {
              const blob = `${w.message_excerpt || ""} ${w.mesaj || ""} ${w.tip || ""}`;
              const m = blob.match(/MESAJ\\s+(\\d+)\\s*\\/\\s*(\\d+)/i);
              if (m) {
                nr = Number(m[1]);
                tot = Number(m[2]);
              }
            }
            if (nr && tot) return `Mesaj ${nr}/${tot}`;
            if (total > 1) return `Mesaj ${index + 1}/${total}`;
            return "";
          };
"""


def patch_label(label: str) -> str:
    if "mesajLabel" in label:
        print("already patched")
        return label

    insert_at = label.find("for (let i = 0; i < warnings.length; i++)")
    if insert_at < 0:
        insert_at = label.find("const escapeHtml")
        if insert_at < 0:
            print("no insertion point")
            return label
        end = label.find("if (!bin || bin.state !==", insert_at)
        if end < 0:
            print("no bin check")
            return label
        label = label[:end] + MESAJ_LABEL_FN + "\n\n          " + label[end:]
    else:
        label = label[:insert_at] + MESAJ_LABEL_FN + "\n\n          " + label[insert_at:]

    candidates = [
        (
            'html += `<div style="font-weight:900;color:${c};text-transform:uppercase;margin-bottom:6px;">${titlu}${badge(w.level)}</div>`;',
            'const mesaj = mesajLabel(w, i, warnings.length);\n      html += `<div style="font-weight:900;color:${c};text-transform:uppercase;margin-bottom:6px;">${titlu}${badge(w.level)}${mesaj ? `<span style="opacity:0.85;margin-left:8px;font-size:12px;font-weight:700;">${mesaj}</span>` : ""}</div>`;',
        ),
        (
            'html += `<div style=\\"font-weight:900;color:${c};text-transform:uppercase;margin-bottom:6px;\\">${titlu}${badge(w.level)}</div>`;',
            'const mesaj = mesajLabel(w, i, warnings.length);\n            html += `<div style=\\"font-weight:900;color:${c};text-transform:uppercase;margin-bottom:6px;\\">${titlu}${badge(w.level)}${mesaj ? `<span style=\\"opacity:0.85;margin-left:8px;font-size:12px;font-weight:700;\\">${mesaj}</span>` : \\"\\"}</div>`;',
        ),
    ]
    for old, new in candidates:
        if old in label:
            label = label.replace(old, new)
            print("title patched")
            return label
    print("title line not found")
    return label


def main() -> None:
    data = json.loads(STORAGE.read_text())
    patched = 0

    def walk(obj):
        nonlocal patched
        if isinstance(obj, dict):
            for k, v in obj.items():
                if (
                    k == "label"
                    and isinstance(v, str)
                    and "mapStyle" in v
                    and "warnings" in v
                ):
                    obj[k] = patch_label(v)
                    patched += 1
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    STORAGE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"cards patched: {patched}")


if __name__ == "__main__":
    main()
