"""Constants for Cod Galben (ANM Meteoromania) integration."""

from __future__ import annotations

DOMAIN = "cod_galben"
NAME = "Cod Galben"

CONF_COUNTY = "county"
CONF_MAP_STYLE = "map_style"

# How Lovelace / cards should show maps (options flow)
MAP_STYLE_OFICIAL = "oficial"  # ANM SVG (harta.svg.php / /local/harta_anm_*.svg)
MAP_STYLE_GIS = "gis"  # Leaflet polygons from coordGis
MAP_STYLE_AMBELE = "ambele"  # both
MAP_STYLE_DEFAULT = MAP_STYLE_OFICIAL

MAP_STYLE_OPTIONS: list[dict[str, str]] = [
    {"value": MAP_STYLE_OFICIAL, "label": "Hartă oficială ANM (SVG)"},
    {"value": MAP_STYLE_GIS, "label": "Hartă GIS (poligoane Leaflet)"},
    {"value": MAP_STYLE_AMBELE, "label": "Ambele (oficial + GIS)"},
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


def normalize_county_token(token: str) -> str | None:
    """Map a free-text county token to ANM code, if known."""
    key = token.strip().casefold()
    return _COUNTY_ALIASES.get(key)


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
