# Cod Galben

Integrare Home Assistant pentru avertizările meteorologice ANM ([meteoromania.ro](https://www.meteoromania.ro/avertizari/)): **atenționări / avertizări**, **informare** (gri) și **nowcasting**, filtrate pe un județ din România.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

## Caracteristici

- Selector de **județ** la instalare (toate cele 42 de unități: județe + București)
- Culori: `galben` / `portocaliu` / `rosu` + `informare` (gri)
- Pe hărți mixte folosește **culoarea zonei județului** din XML (`judet/@culoare`), nu doar culoarea maximă a mesajului
- Poll la **5 minute** (nowcasting + avertizări)
- Exemple de automatizări cu notificare pe telefon

## Instalare

### HACS

1. HACS → Integrations → ⋮ → Custom repositories  
2. URL: `https://github.com/dancucu/ha-cod-galben`  
3. Category: Integration → Add  
4. Caută **Cod Galben** → Download  
5. Restart Home Assistant  

### Manual

Copiază `custom_components/cod_galben` în `/config/custom_components/` și restartează HA.

## Configurare

Settings → Devices & Services → Add Integration → **Cod Galben** → alege județul.

Poți adăuga integrarea de mai multe ori (câte un județ per entry).

### Stil hartă (opțiuni)

După instalare: **Settings → Devices & Services → Cod Galben → Configure**.

Aici alegi **ce tip de hartă** apare pe cardul Lovelace și, pentru Leaflet, **ce fundal** folosește.

#### 1. Tip hartă pe card (`map_style`)

| Opțiune în UI | Valoare | Ce afișează cardul |
|---------------|---------|-------------------|
| **Hartă oficială ANM (SVG)** | `oficial` | harta SVG ANM (ca pe meteoromania.ro) — *default* |
| **Hartă GIS (Leaflet)** | `gis` | poligoane din `coordGis` pe hartă Leaflet interactivă |
| **Ambele (oficial + GIS)** | `ambele` | SVG oficial + hartă Leaflet, una sub alta |

#### 2. Fundal hartă GIS / Leaflet (`gis_basemap`)

Relevant doar când tipul e **GIS** sau **Ambele**:

| Opțiune în UI | Valoare | Fundal |
|---------------|---------|--------|
| **OpenStreetMap (stil leafletjs.com)** | `osm` | tiles OSM clasice — *default* |
| **Relief (OpenTopoMap)** | `topo` | relief / topo |

Exemplu tipic: tip **Hartă GIS (Leaflet)** + fundal **OpenStreetMap**.

#### Cum ajunge setarea pe card

1. Configurezi opțiunile în integrare (pașii de mai sus).
2. Pe `binary_sensor.cod_galben_<judet>_avertizare_activa` apar atributele:
   - `map_style` — `oficial` / `gis` / `ambele`
   - `gis_basemap` — `osm` / `topo`
3. Cardul din [`examples/lovelace_card_avertizare_meteo.yaml`](examples/lovelace_card_avertizare_meteo.yaml) citește aceste atribute și:
   - arată/ascunde SVG-ul oficial și/sau iframe-ul Leaflet;
   - trece fundalul în viewer: `/local/cod_galben/map.html?tiles=osm|topo&src=...`.

Dacă schimbi opțiunile și cardul nu se actualizează, reîncarcă dashboard-ul (sau forțează refresh pe browser).

#### Fișiere generate

Integrarea scrie sub `/config/www/cod_galben/`:

- `gis_{id}.json` — GeoJSON (inclusiv zone munte din SVG ANM, când e cazul)
- `map.html` — viewer Leaflet (local, fără CDN)
- `romania.geojson`, Leaflet JS/CSS — assets pentru hartă

Harta GIS acoperă toată România; județul monitorizat e evidențiat cu contur discret.

## Entități

Device: `Cod Galben {Județ}`

| Tip | Nume | Descriere |
|-----|------|-----------|
| binary_sensor | Avertizare activă | `on` dacă județul e pe hartă (inclusiv informare) |
| sensor | Nivel avertizare | `none` / `informare` / `galben` / `portocaliu` / `rosu` |
| sensor | Fenomene | fenomenele asociate |
| sensor | Valabil de la / până la | interval ISO |
| sensor | Interval avertizare | text ANM |
| sensor | Tip mesaj | Atenționare / Avertizare / Informare |
| sensor | Număr mesaje | câte mesaje afectează județul |
| binary_sensor | Nowcasting activ | nowcasting pentru județ |
| sensor | Nivel / Fenomene / Interval nowcasting | analog |

Atribute utile pe binary sensor / nivel: `mesaj` (text detaliat ANM), `warnings` (listă cu `mesaj` / `fenomene` / interval per mesaj), `judet`, `judet_nume`, `map_style`, `gis_basemap`, `map_ids`.

## API folosite

- `https://www.meteoromania.ro/avertizari-xml.php`
- `https://www.meteoromania.ro/avertizari-nowcasting-xml.php`
- `https://www.meteoromania.ro/avertizari-nowcasting-xml-gis.php`

## Card Lovelace „AVERTIZARE METEO”

Replică stilul cardului din dashboard-ul **Acasă** (ha-lenovo): antet colorat + fold cu detalii.

| Fișier | Dependențe |
|--------|------------|
| [`examples/lovelace_card_avertizare_meteo.yaml`](examples/lovelace_card_avertizare_meteo.yaml) | HACS: **button-card**, **fold-entity-row** |
| [`examples/lovelace_card_markdown.yaml`](examples/lovelace_card_markdown.yaml) | doar Markdown nativ |

Culori antet: galben `#ffde07` / portocaliu `#f09035` / roșu `#ea3323` / informare gri / idle albastru. Expandat: tip, interval, fenomene, **detalii** (textul ANM cu temperaturi / precipitații din atributul XML `mesaj`) + hărți conform opțiunilor din Configure + nowcasting dacă e activ. Tap pe detalii → [meteoromania.ro/avertizari](https://www.meteoromania.ro/avertizari/).

## Automatizări

Vezi [`examples/`](examples/).

Înlocuiește:

1. `notify.mobile_app_telefonul_tau` cu serviciul tău Companion App  
2. entity_id-urile cu cele din Developer Tools (conțin slug-ul județului, ex. `galati`)

Exemplu (Galați) — avertizare:

```yaml
triggers:
  - trigger: state
    entity_id: binary_sensor.cod_galben_galati_avertizare_activa
    to: "on"
actions:
  - action: notify.mobile_app_iphone
    data:
      title: "Cod {{ states('sensor.cod_galben_galati_nivel_avertizare') }}"
      message: >-
        Perioadă: {{ states('sensor.cod_galben_galati_interval_avertizare') }}
        Fenomene: {{ states('sensor.cod_galben_galati_fenomene') }}
```

## Logică culori (zone)

| `judet/@culoare` | Nivel |
|------------------|-------|
| 1 | galben |
| 2 | portocaliu |
| 3 | roșu |

Informările naționale (tip mesaj „Informare”) marchează județul ca afectat cu nivel `informare`.

## Disclaimer

Proiect comunitar, neafiliat ANM. Datele aparțin Administrației Naționale de Meteorologie.

## Licență

MIT
