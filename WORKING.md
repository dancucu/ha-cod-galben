# Cod Galben — memorie de lucru (Home Assistant)

**Repo:** `dancucu/ha-cod-galben` (GitHub)  
**Cale locală:** `/Users/dan/Obsidian/cod galben/ha-cod-galben`  
**Status:** în curs — integrare custom HA pe API Meteoromania

## Cerință (utilizator)

Integrare Home Assistant numită **„Cod Galben”** care:

1. Citește avertizările ANM (XML) + nowcasting (XML/GIS).
2. Are **selector de județ** (orice județ din România).
3. Expune senzorii necesari (nivel, culoare, perioadă, fenomene, afectat da/nu).
4. Culori: **galben / portocaliu / roșu** + **informare** (gri, de obicei națională).
5. Exemple de automatizare → notificare telefon (culoare, perioadă, fenomene) pentru:
   - avertizări generale
   - nowcasting

## Surse API (oficiale)

| Endpoint | Rol |
|----------|-----|
| `https://www.meteoromania.ro/avertizari-xml.php` | Atenționări/avertizări + poligoane `judet`/`coordGis` |
| `https://www.meteoromania.ro/avertizari-nowcasting-xml.php` | Nowcasting (atribute pe `<avertizare>`) |
| `https://www.meteoromania.ro/avertizari-nowcasting-xml-gis.php` | Nowcasting cu GIS (când există) |

Alternativ JSON (aceeași logică județe): `wp-json/meteoapi/v2/avertizari-generale`

## Logică culori (stabilită 19 iul 2026)

### Pe zone (`<judet culoare=…>`) — harta mixtă

- `1` = **galben**
- `2` = **portocaliu**
- `3` = **roșu**
- `0` = adesea zonă specială / informare / nefolosit pe hartă mixtă

Județul e afectat de un cod dacă există `judet` cu `cod` egal sau prefix (`GL`, `GL_munte` → județ `GL`) **și** culoarea zonei e galben/portocaliu/roșu.

Pe hărți mixte: **nu** folosi doar `culoare` de pe `<avertizare>` (aceea e adesea maximul pe hartă). Folosește culoarea zonei județului.

### Pe `<avertizare>` (overall / nowcasting fără zone)

- `0` = galben, `1` = portocaliu, `2` = roșu (scara nowcasting / overall)
- **Informare:** `numeTipMesaj` conține „Informare” sau tip dedicat → nivel `informare` (gri); de obicei toată țara → județul selectat e considerat afectat.

### Severitate (max)

`rosu` > `portocaliu` > `galben` > `informare` > `none`

## Entități țintă

Prefix device: județul ales (ex. Galați).

| Entity | Rol |
|--------|-----|
| `binary_sensor.cod_galben_afectat` | Există avertizare relevantă pentru județ |
| `sensor.cod_galben_nivel` | none / informare / galben / portocaliu / rosu |
| `sensor.cod_galben_fenomene` | text fenomene (cel mai sever / agregat) |
| `sensor.cod_galben_valabil_de` | început |
| `sensor.cod_galben_valabil_pana` | sfârșit |
| `sensor.cod_galben_tip` | Atenționare / Avertizare / Informare |
| `sensor.cod_galben_mesaje` | număr mesaje active pentru județ |
| `binary_sensor.cod_galben_nowcasting_afectat` | nowcasting activ |
| `sensor.cod_galben_nowcasting_nivel` | … |
| `sensor.cod_galben_nowcasting_fenomene` | … |
| `sensor.cod_galben_nowcasting_valabil_de` / `_pana` | … |

Atribute pe senzori: listă completă `warnings` / `alerts`.

## Intervale poll

- Avertizări generale: **15 min**
- Nowcasting: **5 min** (sau același coordinator cu min 5 min)

## Structură repo

```
ha-cod-galben/
├── WORKING.md                          # acest fișier
├── README.md
├── LICENSE
├── hacs.json
├── examples/
│   ├── automation_avertizare.yaml
│   └── automation_nowcasting.yaml
└── custom_components/cod_galben/
    ├── __init__.py
    ├── manifest.json
    ├── const.py
    ├── config_flow.py
    ├── coordinator.py
    ├── sensor.py
    ├── binary_sensor.py
    ├── strings.json
    └── translations/{en,ro}.json
```

## Pași rămase / checklist reluare

- [x] Proiect local + git init (`create_project`)
- [x] Scaffold `custom_components/cod_galben/*`
- [x] Parser XML avertizări + nowcasting
- [x] Config flow selector județ
- [x] Senzori + binary sensors
- [x] Exemple automatizări notificare
- [x] README + HACS
- [ ] Creare repo GitHub `ha-cod-galben` + push
- [ ] (opțional) Instalare pe HA lenovo / test live

## Context conversație

- Analiză API pe `meteoromania.ro/avertizari/`
- Demo local: `../meteo-galati/` (hărți GL)
- Utilizatorul a corectat: mesajul 2/5 mixt — Galați e **galben** pe zonă (`culoare=1`), nu portocaliu

## Reluare după întrerupere

1. Citește acest `WORKING.md`.
2. Continuă de la primul checkbox nebifat.
3. Nu reinventă maparea culorilor pe zone — e deja validată.
