#!/usr/bin/env python3
"""Highlight county / ANM subregion in AVERTIZARE METEO Detalii text."""
from __future__ import annotations

import json
from pathlib import Path

HIGHLIGHT_FN = """
          const escapeHtml = (s) => String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');

          const highlightLocal = (text, color, names, bareNames) => {
            const escaped = escapeHtml(text);
            if (!escaped) return '';
            const skipBefore = /(?:nord-estul|nord-vestul|sud-estul|sud-vestul|nordul|sudul|estul|vestul)\\s+$/i;
            const isWord = (ch) => ch && /[0-9A-Za-zĂÂÎȘȚăâîșțŞşŢţ]/.test(ch);
            const all = [];
            (names || []).forEach((n) => { const s = String(n || '').trim(); if (s) all.push({ s, bare: false }); });
            (bareNames || []).forEach((n) => { const s = String(n || '').trim(); if (s) all.push({ s, bare: true }); });
            all.sort((a, b) => b.s.length - a.s.length);
            const ranges = [];
            const lower = escaped.toLowerCase();
            for (const item of all) {
              const needle = escapeHtml(item.s);
              const nl = needle.toLowerCase();
              if (!nl) continue;
              let from = 0;
              while (from <= lower.length - nl.length) {
                const idx = lower.indexOf(nl, from);
                if (idx < 0) break;
                from = idx + 1;
                const beforeCh = idx === 0 ? '' : escaped[idx - 1];
                const afterCh = idx + needle.length >= escaped.length ? '' : escaped[idx + needle.length];
                if (isWord(beforeCh) || isWord(afterCh)) continue;
                if (ranges.some((r) => !(idx + needle.length <= r.start || idx >= r.end))) continue;
                if (item.bare) {
                  const prefix = escaped.slice(Math.max(0, idx - 24), idx);
                  if (skipBefore.test(prefix)) continue;
                }
                ranges.push({ start: idx, end: idx + needle.length });
              }
            }
            ranges.sort((a, b) => a.start - b.start);
            let out = '';
            let cursor = 0;
            const open = `<b style="color:${color};font-weight:800;">`;
            for (const r of ranges) {
              out += escaped.slice(cursor, r.start) + open + escaped.slice(r.start, r.end) + '</b>';
              cursor = r.end;
            }
            return out + escaped.slice(cursor);
          };

"""

DETALII_OLD = "Detalii:</b> ${detalii}"
DETALII_NEW = (
    "Detalii:</b> ${highlightLocal(detalii, c, "
    "bin?.attributes?.highlight_names || "
    "['sud-estul Moldovei', 'sudul Moldovei', 'Galațiului', 'Galatiului', judet, 'Galati'], "
    "bin?.attributes?.highlight_bare_names || ['Moldovei', 'Moldova'])}"
)
DETALII_ESCAPED_OLD = "Detalii:</b> ${escapeHtml(detalii)}"


def patch_label(label: str) -> str:
    if "highlightLocal" not in label:
        insert_at = label.find("const mesajLabel")
        if insert_at < 0:
            insert_at = label.find("if (!bin || bin.state")
        if insert_at < 0:
            print("no insertion point")
            return label
        label = label[:insert_at] + HIGHLIGHT_FN + "\n          " + label[insert_at:]

    if DETALII_NEW in label:
        return label
    if DETALII_ESCAPED_OLD in label:
        return label.replace(DETALII_ESCAPED_OLD, DETALII_NEW)
    if DETALII_OLD in label:
        return label.replace(DETALII_OLD, DETALII_NEW)
    print("detalii line not found")
    return label


def patch_file(path: Path) -> int:
    data = json.loads(path.read_text())
    patched = 0

    def walk(obj):
        nonlocal patched
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "label" and isinstance(v, str) and "Detalii:" in v and "warnings" in v:
                    new_v = patch_label(v)
                    if new_v != v:
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
