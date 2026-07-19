"""Leaflet GIS map viewer for Cod Galben (local assets, no CDN).

Served from /local/cod_galben/map.html?src=/local/cod_galben/gis_4185.json
Leaflet JS/CSS are copied next to this file by www_store.
"""

from __future__ import annotations

MAP_HTML = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cod Galben — hartă GIS</title>
<link rel="stylesheet" href="leaflet.css"/>
<style>
  html, body { margin:0; height:100%; background:#fff; }
  #map { width:100%; height:100%; background:#f5f5f5; }
  .err { color:#333; font-family:system-ui,sans-serif; padding:1rem; }
  .leaflet-container { background:#f0f4f8; font: 12px/1.4 system-ui,sans-serif; }
</style>
</head>
<body>
<div id="map"></div>
<script src="leaflet.js"></script>
<script>
(async function () {
  const FILL = { galben:'#fdd835', portocaliu:'#fb8c00', rosu:'#e53935', alt:'#cfd8dc' };
  const EDGE = { galben:'#f9a825', portocaliu:'#ef6c00', rosu:'#b71c1c', alt:'#90a4ae' };
  // Full Romania — same framing idea as harta oficială ANM
  const ROMANIA = L.latLngBounds([43.55, 20.15], [48.30, 29.75]);

  const params = new URLSearchParams(location.search);
  let src = params.get('src');
  if (!src) {
    document.body.innerHTML = '<div class="err">Lipsește parametrul src=</div>';
    return;
  }
  if (!(src.startsWith('/') || src.startsWith('http'))) {
    src = location.pathname.replace(/[^/]+$/, '') + src;
  }
  // Prefer GeoJSON for Leaflet (svg companion is fallback only)
  if (src.endsWith('.svg')) src = src.slice(0, -4) + '.json';

  let geojson;
  try {
    const r = await fetch(src, { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    geojson = await r.json();
  } catch (e) {
    document.body.innerHTML = '<div class="err">Nu pot încărca ' + src + ': ' + e + '</div>';
    return;
  }

  const map = L.map('map', {
    zoomControl: true,
    attributionControl: true,
    maxBounds: ROMANIA.pad(0.15),
    maxBoundsViscosity: 0.6,
  });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 12,
    minZoom: 5,
  }).addTo(map);

  const layer = L.geoJSON(geojson, {
    style: f => {
      const p = f.properties || {};
      const n = p.culoareNume || 'alt';
      const sel = p.isSelected || p.isGalati;
      return {
        color: sel ? '#bf360c' : (EDGE[n] || EDGE.alt),
        weight: sel ? 3 : 1,
        fillColor: FILL[n] || FILL.alt,
        fillOpacity: sel ? 0.75 : 0.45,
      };
    },
    onEachFeature: (f, l) => {
      const p = f.properties || {};
      const label = (p.nume || p.cod || '') + (p.culoareNume ? (': ' + p.culoareNume) : '');
      l.bindPopup(label);
      // county code tooltip on hover
      if (p.cod_base || p.cod) {
        l.bindTooltip(p.cod_base || String(p.cod).split('_')[0], {
          permanent: false, direction: 'center', className: 'county-tip'
        });
      }
    }
  }).addTo(map);

  // Always show entire Romania (like official ANM SVG), not just warning bbox
  map.fitBounds(ROMANIA, { padding: [8, 8], maxZoom: 7 });
  setTimeout(() => map.invalidateSize(), 50);
})();
</script>
</body>
</html>
"""
