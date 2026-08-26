"""Constants for Cod Galben (ANM Meteoromania) integration."""

from __future__ import annotations

DOMAIN = "cod_galben"
NAME = "Cod Galben"

CONF_COUNTY = "county"
CONF_MAP_STYLE = "map_style"
CONF_GIS_BASEMAP = "gis_basemap"

# How Lovelace / cards should show maps (options flow)
MAP_STYLE_OFICIAL = "oficial"  # ANM SVG (harta.svg.php / /local/harta_anm_*.svg)
MAP_STYLE_GIS = "gis"  # Leaflet polygons from coordGis
MAP_STYLE_AMBELE = "ambele"  # both
MAP_STYLE_DEFAULT = MAP_STYLE_OFICIAL

MAP_STYLE_OPTIONS: list[dict[str, str]] = [
    {"value": MAP_STYLE_OFICIAL, "label": "Hartă oficială ANM (SVG)"},
    {"value": MAP_STYLE_GIS, "label": "Hartă GIS (Leaflet)"},
    {"value": MAP_STYLE_AMBELE, "label": "Ambele (oficial + GIS)"},
]

# Leaflet tile layer when GIS / ambele is selected
GIS_BASEMAP_OSM = "osm"  # OpenStreetMap — ca pe leafletjs.com
GIS_BASEMAP_TOPO = "topo"  # OpenTopoMap — relief
GIS_BASEMAP_DEFAULT = GIS_BASEMAP_OSM

GIS_BASEMAP_OPTIONS: list[dict[str, str]] = [
    {"value": GIS_BASEMAP_OSM, "label": "OpenStreetMap (stil leafletjs.com)"},
    {"value": GIS_BASEMAP_TOPO, "label": "Relief (OpenTopoMap)"},
]

WWW_GIS_DIR = "cod_galben"
WWW_GIS_MAP_HTML = "map.html"

URL_AVERTIZARI = "https://www.meteoromania.ro/avertizari-xml.php"
URL_AVERTIZARI_PAGE = "https://www.meteoromania.ro/avertizari/"
URL_HARTA_SVG = (
    "https://www.meteoromania.ro/wp-content/plugins/meteo/harti/"
    "harta.svg.php?id_avertizare={id}"
)
URL_NOWCASTING = "https://www.meteoromania.ro/avertizari-nowcasting-xml.php"
URL_NOWCASTING_GIS = "https://www.meteoromania.ro/avertizari-nowcasting-xml-gis.php"

# Poll: nowcasting needs to be fresher than general warnings
UPDATE_INTERVAL_SECONDS = 300  # 5 minutes

# Zone-level colours on <judet culoare="…"> (mixed maps) — validated Jul 2026
ZONE_COLOR_CODES: dict[str, str] = {
    "1": "galben",
    "2": "portocaliu",
    "3": "rosu",
}

# Overall / nowcasting attribute culoare on <avertizare>
OVERALL_COLOR_CODES: dict[str, str] = {
    "0": "galben",
    "1": "portocaliu",
    "2": "rosu",
}

LEVEL_NONE = "none"
LEVEL_INFORMARE = "informare"
LEVEL_GALBEN = "galben"
LEVEL_PORTOCALIU = "portocaliu"
LEVEL_ROSU = "rosu"

SEVERITY_RANK: dict[str, int] = {
    LEVEL_NONE: 0,
    LEVEL_INFORMARE: 1,
    LEVEL_GALBEN: 2,
    LEVEL_PORTOCALIU: 3,
    LEVEL_ROSU: 4,
}

LEVEL_ICONS: dict[str, str] = {
    LEVEL_NONE: "mdi:check-circle-outline",
    LEVEL_INFORMARE: "mdi:information-outline",
    LEVEL_GALBEN: "mdi:alert-outline",
    LEVEL_PORTOCALIU: "mdi:alert",
    LEVEL_ROSU: "mdi:alert-octagon",
}

# cod ANM → etichetă UI
JUDETE: dict[str, str] = {
    "AB": "Alba",
    "AR": "Arad",
    "AG": "Argeș",
    "BC": "Bacău",
    "BH": "Bihor",
    "BN": "Bistrița-Năsăud",
    "BT": "Botoșani",
    "BV": "Brașov",
    "BR": "Brăila",
    "B": "București",
    "BZ": "Buzău",
    "CS": "Caraș-Severin",
    "CL": "Călărași",
    "CJ": "Cluj",
    "CT": "Constanța",
    "CV": "Covasna",
    "DB": "Dâmbovița",
    "DJ": "Dolj",
    "GL": "Galați",
    "GR": "Giurgiu",
    "GJ": "Gorj",
    "HR": "Harghita",
    "HD": "Hunedoara",
    "IL": "Ialomița",
    "IS": "Iași",
    "IF": "Ilfov",
    "MM": "Maramureș",
    "MH": "Mehedinți",
    "MS": "Mureș",
    "NT": "Neamț",
    "OT": "Olt",
    "PH": "Prahova",
    "SM": "Satu Mare",
    "SJ": "Sălaj",
    "SB": "Sibiu",
    "SV": "Suceava",
    "TR": "Teleorman",
    "TM": "Timiș",
    "TL": "Tulcea",
    "VS": "Vaslui",
    "VL": "Vâlcea",
    "VN": "Vrancea",
}

# Nume județ (cu/fără diacritice) → cod, pentru matching nowcasting text
_COUNTY_ALIASES: dict[str, str] = {}
for _code, _name in JUDETE.items():
    _COUNTY_ALIASES[_name.casefold()] = _code
    _COUNTY_ALIASES[_code.casefold()] = _code

# aliasuri frecvente în textul ANM
_COUNTY_ALIASES.update(
    {
        "bucuresti": "B",
        "bucurești": "B",
        "municipiul bucurești": "B",
        "municipiul bucuresti": "B",
        "galati": "GL",
        "galați": "GL",
        "iasi": "IS",
        "iași": "IS",
        "brasov": "BV",
        "brașov": "BV",
        "timis": "TM",
        "timiș": "TM",
        "constanta": "CT",
        "constanța": "CT",
        "dambovita": "DB",
        "dâmbovița": "DB",
        "valcea": "VL",
        "vâlcea": "VL",
        "salaj": "SJ",
        "sălaj": "SJ",
        "calarasii": "CL",
        "călărași": "CL",
        "calarasi": "CL",
        "arges": "AG",
        "argeș": "AG",
        "bacau": "BC",
        "bacău": "BC",
        "botosani": "BT",
        "botoșani": "BT",
        "braila": "BR",
        "brăila": "BR",
        "buzau": "BZ",
        "buzău": "BZ",
        "caras-severin": "CS",
        "caraș-severin": "CS",
        "covasna": "CV",
        "giurgiu": "GR",
        "gorj": "GJ",
        "harghita": "HR",
        "hunedoara": "HD",
        "ialomita": "IL",
        "ialomița": "IL",
        "ilfov": "IF",
        "maramures": "MM",
        "maramureș": "MM",
        "mehedinti": "MH",
        "mehedinți": "MH",
        "mures": "MS",
        "mureș": "MS",
        "neamt": "NT",
        "neamț": "NT",
        "olt": "OT",
        "prahova": "PH",
        "satu mare": "SM",
        "sibiu": "SB",
        "suceava": "SV",
        "teleorman": "TR",
        "tulcea": "TL",
        "vaslui": "VS",
        "vrancea": "VN",
        "alba": "AB",
        "arad": "AR",
        "bihor": "BH",
        "bistrita-nasaud": "BN",
        "bistrița-năsăud": "BN",
        "cluj": "CJ",
        "dolj": "DJ",
    }
)


def county_label(code: str) -> str:
    """Return display name for a county code."""
    return JUDETE.get(code, code)


# ASCII fold for ANM texts that omit diacritics (Galați → Galati).
_DIACRITIC_TABLE = str.maketrans(
    {
        "ă": "a",
        "â": "a",
        "î": "i",
        "ș": "s",
        "ț": "t",
        "Ă": "A",
        "Â": "A",
        "Î": "I",
        "Ș": "S",
        "Ț": "T",
        "ş": "s",
        "ţ": "t",
        "Ş": "S",
        "Ţ": "T",
    }
)

# Articulated / genitive forms as they appear in ANM copy („județului Galațiului”).
COUNTY_GENITIVE: dict[str, list[str]] = {
    "AB": ["Albei"],
    "AR": ["Aradului"],
    "AG": ["Argeșului"],
    "BC": ["Bacăului"],
    "BH": ["Bihorului"],
    "BN": ["Bistriței-Năsăud", "Bistrița-Năsăudului"],
    "BT": ["Botoșaniului"],
    "BV": ["Brașovului"],
    "BR": ["Brăilei"],
    "B": ["Bucureștiului"],
    "BZ": ["Buzăului"],
    "CS": ["Caraș-Severinului"],
    "CL": ["Călărașiului"],
    "CJ": ["Clujului"],
    "CT": ["Constanței"],
    "CV": ["Covasnei"],
    "DB": ["Dâmboviței"],
    "DJ": ["Doljului"],
    "GL": ["Galațiului"],
    "GR": ["Giurgiului"],
    "GJ": ["Gorjului"],
    "HR": ["Harghitei"],
    "HD": ["Hunedoarei"],
    "IL": ["Ialomiței"],
    "IS": ["Iașului"],
    "IF": ["Ilfovului"],
    "MM": ["Maramureșului"],
    "MH": ["Mehedințiului"],
    "MS": ["Mureșului"],
    "NT": ["Neamțului"],
    "OT": ["Oltului"],
    "PH": ["Prahovei"],
    "SM": ["Satu Mare"],
    "SJ": ["Sălajului"],
    "SB": ["Sibiului"],
    "SV": ["Sucevei"],
    "TR": ["Teleormanului"],
    "TM": ["Timișului"],
    "TL": ["Tulcei"],
    "VS": ["Vasluiului"],
    "VL": ["Vâlcii"],
    "VN": ["Vrancei"],
}

_MOLDOVA_BARE = ["Moldova", "Moldovei"]
_MUNTENIA_BARE = ["Muntenia", "Munteniei"]
_OLTENIA_BARE = ["Oltenia", "Olteniei"]
_TRANSILVANIA_BARE = ["Transilvania", "Transilvaniei"]
_BANAT_BARE = ["Banat", "Banatului"]
_CRISANA_BARE = ["Crișana", "Crișanei"]
_MARAMURES_BARE = ["Maramureș", "Maramureșului"]
_DOBROGEA_BARE = ["Dobrogea", "Dobrogei"]

# Subregion phrases that mean this county's area is affected (longest match first).
# Do not list other parts of the same macro-region (GL ≠ nord-estul Moldovei).
COUNTY_SUBREGION_PHRASES: dict[str, list[str]] = {
    "GL": ["sud-estul Moldovei", "sudul Moldovei"],
    "VN": ["sudul Moldovei", "sud-vestul Moldovei"],
    "VS": ["estul Moldovei", "sud-estul Moldovei"],
    "BC": ["centrul Moldovei"],
    "IS": ["nord-estul Moldovei", "nordul Moldovei"],
    "BT": ["nord-estul Moldovei", "nordul Moldovei"],
    "SV": ["nordul Moldovei", "nord-vestul Moldovei"],
    "NT": ["nordul Moldovei", "centrul Moldovei"],
    "BR": ["nord-estul Munteniei", "estul Munteniei"],
    "BZ": ["nord-estul Munteniei", "nordul Munteniei"],
    "PH": ["nordul Munteniei"],
    "DB": ["nordul Munteniei"],
    "AG": ["nordul Munteniei", "nord-vestul Munteniei"],
    "IL": ["estul Munteniei", "sud-estul Munteniei"],
    "CL": ["sud-estul Munteniei", "sudul Munteniei"],
    "GR": ["sudul Munteniei"],
    "TR": ["sudul Munteniei"],
    "B": ["sudul Munteniei"],
    "IF": ["sudul Munteniei"],
    "DJ": ["sudul Olteniei"],
    "MH": ["sud-vestul Olteniei", "vestul Olteniei"],
    "OT": ["estul Olteniei"],
    "GJ": ["nordul Olteniei"],
    "VL": ["nordul Olteniei", "nord-estul Olteniei"],
    "CT": ["litoralul Mării Negre", "estul Dobrogei"],
    "TL": ["nordul Dobrogei", "Delta Dunării"],
}

COUNTY_REGION_BARE: dict[str, list[str]] = {
    "BT": _MOLDOVA_BARE,
    "SV": _MOLDOVA_BARE,
    "NT": _MOLDOVA_BARE,
    "IS": _MOLDOVA_BARE,
    "BC": _MOLDOVA_BARE,
    "VS": _MOLDOVA_BARE,
    "VN": _MOLDOVA_BARE,
    "GL": _MOLDOVA_BARE,
    "AG": _MUNTENIA_BARE,
    "DB": _MUNTENIA_BARE,
    "PH": _MUNTENIA_BARE,
    "BZ": _MUNTENIA_BARE,
    "BR": _MUNTENIA_BARE,
    "IL": _MUNTENIA_BARE,
    "CL": _MUNTENIA_BARE,
    "GR": _MUNTENIA_BARE,
    "TR": _MUNTENIA_BARE,
    "IF": _MUNTENIA_BARE,
    "B": _MUNTENIA_BARE,
    "DJ": _OLTENIA_BARE,
    "GJ": _OLTENIA_BARE,
    "MH": _OLTENIA_BARE,
    "OT": _OLTENIA_BARE,
    "VL": _OLTENIA_BARE,
    "AB": _TRANSILVANIA_BARE,
    "BN": _TRANSILVANIA_BARE,
    "BV": _TRANSILVANIA_BARE,
    "CJ": _TRANSILVANIA_BARE,
    "CV": _TRANSILVANIA_BARE,
    "HR": _TRANSILVANIA_BARE,
    "HD": _TRANSILVANIA_BARE,
    "MS": _TRANSILVANIA_BARE,
    "SB": _TRANSILVANIA_BARE,
    "SJ": _TRANSILVANIA_BARE,
    "TM": _BANAT_BARE,
    "CS": _BANAT_BARE,
    "AR": [*_BANAT_BARE, *_CRISANA_BARE],
    "BH": _CRISANA_BARE,
    "SM": [*_CRISANA_BARE, *_MARAMURES_BARE],
    "MM": _MARAMURES_BARE,
    "CT": _DOBROGEA_BARE,
    "TL": _DOBROGEA_BARE,
}

# Short label for the binary_sensor `regiune` attribute.
COUNTY_REGIUNE: dict[str, str] = {
    "GL": "sudul Moldovei",
    "VN": "sudul Moldovei",
    "VS": "estul Moldovei",
    "BC": "centrul Moldovei",
    "IS": "nord-estul Moldovei",
    "BT": "nord-estul Moldovei",
    "SV": "nordul Moldovei",
    "NT": "nordul Moldovei",
    "BR": "nord-estul Munteniei",
    "BZ": "nord-estul Munteniei",
    "PH": "nordul Munteniei",
    "DB": "nordul Munteniei",
    "AG": "nordul Munteniei",
    "IL": "estul Munteniei",
    "CL": "sudul Munteniei",
    "GR": "sudul Munteniei",
    "TR": "sudul Munteniei",
    "B": "sudul Munteniei",
    "IF": "sudul Munteniei",
    "DJ": "sudul Olteniei",
    "MH": "vestul Olteniei",
    "OT": "estul Olteniei",
    "GJ": "nordul Olteniei",
    "VL": "nordul Olteniei",
    "CT": "Dobrogea",
    "TL": "Dobrogea",
    "TM": "Banat",
    "CS": "Banat",
    "AR": "Banat",
    "BH": "Crișana",
    "SM": "Crișana",
    "MM": "Maramureș",
    "AB": "Transilvania",
    "BN": "Transilvania",
    "BV": "Transilvania",
    "CJ": "Transilvania",
    "CV": "Transilvania",
    "HR": "Transilvania",
    "HD": "Transilvania",
    "MS": "Transilvania",
    "SB": "Transilvania",
    "SJ": "Transilvania",
}


def fold_ascii(text: str) -> str:
    """Strip Romanian diacritics for matching ANM text without them."""
    return (text or "").translate(_DIACRITIC_TABLE)


# Register ASCII-folded county names (cedilla vs comma-below, missing diacritics).
for _code, _name in JUDETE.items():
    _COUNTY_ALIASES[fold_ascii(_name).casefold()] = _code
for _alias, _code in list(_COUNTY_ALIASES.items()):
    _COUNTY_ALIASES[fold_ascii(_alias).casefold()] = _code


def _with_ascii_variants(phrases: list[str]) -> list[str]:
    """Unique phrases plus ASCII folds, longest first."""
    seen: set[str] = set()
    out: list[str] = []
    for phrase in phrases:
        if not phrase:
            continue
        for variant in (phrase, fold_ascii(phrase)):
            key = variant.casefold()
            if not variant or key in seen:
                continue
            seen.add(key)
            out.append(variant)
    out.sort(key=lambda item: (-len(item), item.casefold()))
    return out


def county_highlight_data(code: str) -> dict[str, str | list[str]]:
    """Names/phrases to bold in warning details for this county.

    ``highlight_names`` — county + genitive + subregion phrases (e.g. sudul Moldovei).
    ``highlight_bare_names`` — unqualified macro-region (Moldova) when the whole
    region is listed; the card must skip these after nordul/nord-estul/…
    """
    base = base_judet_code(code)
    label = county_label(base) if base in JUDETE else (code or "")
    names = _with_ascii_variants(
        [label, *COUNTY_GENITIVE.get(base, []), *COUNTY_SUBREGION_PHRASES.get(base, [])]
    )
    name_keys = {item.casefold() for item in names}
    bare = [
        item
        for item in _with_ascii_variants(list(COUNTY_REGION_BARE.get(base, [])))
        if item.casefold() not in name_keys
    ]
    regiune = COUNTY_REGIUNE.get(base) or (
        COUNTY_REGION_BARE.get(base, [""])[0] if COUNTY_REGION_BARE.get(base) else ""
    )
    return {
        "regiune": regiune,
        "highlight_names": names,
        "highlight_bare_names": bare,
    }


def normalize_county_token(token: str) -> str | None:
    """Map a free-text county token to ANM code, if known."""
    key = token.strip().casefold()
    if key in _COUNTY_ALIASES:
        return _COUNTY_ALIASES[key]
    folded = fold_ascii(key)
    return _COUNTY_ALIASES.get(folded)


def base_judet_code(cod: str) -> str:
    """GL_munte / CT_litoral → GL / CT."""
    return (cod or "").split("_", 1)[0].upper()


def max_level(levels: list[str]) -> str:
    """Return highest severity among levels."""
    best = LEVEL_NONE
    best_rank = 0
    for level in levels:
        rank = SEVERITY_RANK.get(level, 0)
        if rank > best_rank:
            best = level
            best_rank = rank
    return best
