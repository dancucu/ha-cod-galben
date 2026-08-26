#!/usr/bin/env python3
"""Regression: Galații Bistriței must not match județul Galați."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "cod_galben"


def _stub_homeassistant() -> None:
    ha = types.ModuleType("homeassistant")
    ha_util = types.ModuleType("homeassistant.util")
    dt = types.ModuleType("homeassistant.util.dt")

    def as_local(value: datetime) -> datetime:
        return value

    def parse_datetime(value: str) -> datetime | None:
        for fmt in (
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d.%m.%Y %H:%M",
        ):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    dt.as_local = as_local  # type: ignore[attr-defined]
    dt.parse_datetime = parse_datetime  # type: ignore[attr-defined]
    ha_util.dt = dt  # type: ignore[attr-defined]
    ha.util = ha_util  # type: ignore[attr-defined]
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.util"] = ha_util
    sys.modules["homeassistant.util.dt"] = dt


def _load_api():
    _stub_homeassistant()
    pkg = types.ModuleType("cod_galben")
    pkg.__path__ = [str(PKG)]  # type: ignore[attr-defined]
    sys.modules["cod_galben"] = pkg

    for name in ("const", "gis", "api"):
        mod_name = f"cod_galben.{name}"
        spec = importlib.util.spec_from_file_location(mod_name, PKG / f"{name}.py")
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        setattr(pkg, name, mod)
        spec.loader.exec_module(mod)

    return sys.modules["cod_galben.api"]


api = _load_api()
extract_counties_from_zona = api.extract_counties_from_zona
parse_nowcasting_xml = api.parse_nowcasting_xml

BN_ZONA = (
    "Județul Bistriţa-Năsăud: Beclean, Teaca, Lechința, Chiochiș, Braniștea, "
    "Nușeni, Matei, Galații Bistriței, Urmeniș, Budești, Sânmihaiu de Câmpie, "
    "Milaș, Miceștii de Câmpie, Silivașu de Câmpie;<br>"
)
GL_ZONA = "Județul Galaţi: Galați, Vânători, Șendreni;<br>"
# Raw '<' in attribute values is invalid XML — ANM uses entities.
BN_ZONA_XML = BN_ZONA.replace("<", "&lt;").replace(">", "&gt;")
GL_ZONA_XML = GL_ZONA.replace("<", "&lt;").replace(">", "&gt;")


def test_extract() -> None:
    assert extract_counties_from_zona(BN_ZONA) == ["BN"], extract_counties_from_zona(
        BN_ZONA
    )
    assert extract_counties_from_zona(GL_ZONA) == ["GL"], extract_counties_from_zona(
        GL_ZONA
    )


def test_parse_gl_only() -> None:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<avertizariNowcasting>
  <avertizare numeTipMesaj="Atentionare nowcasting" tipMesaj="2"
    numeCuloare="galben" culoare="2"
    zona="{BN_ZONA_XML}"
    semnalare="Averse BN"
    dataInceput="26.08.2026 17:45" dataSfarsit="26.08.2026 19:00"/>
  <avertizare numeTipMesaj="Atentionare nowcasting" tipMesaj="2"
    numeCuloare="galben" culoare="2"
    zona="{GL_ZONA_XML}"
    semnalare="Averse GL"
    dataInceput="26.08.2026 17:15" dataSfarsit="26.08.2026 18:15"/>
  <avertizare numeTipMesaj="Atentionare nowcasting" tipMesaj="2"
    numeCuloare="galben" culoare="2"
    zona="{BN_ZONA_XML}"
    semnalare="Averse BN2"
    dataInceput="26.08.2026 16:40" dataSfarsit="26.08.2026 19:00"/>
</avertizariNowcasting>
"""
    hits = parse_nowcasting_xml(xml, "GL")
    assert len(hits) == 1, [(h.zona[:40], h.judet_codes) for h in hits]
    assert "Galaţi" in hits[0].zona or "Galați" in hits[0].zona
    assert hits[0].judet_codes == ["GL"]


if __name__ == "__main__":
    test_extract()
    test_parse_gl_only()
    print("ok")
