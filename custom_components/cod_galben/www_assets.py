"""Leaflet GIS map viewer for Cod Galben (served from /local/cod_galben/).

Usage: /local/cod_galben/map.html?src=gis_4185.json&county=GL
"""

from __future__ import annotations

MAP_HTML = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cod Galben — hartă GIS</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html, body { margin:0; height:100%; background:#111; }
  #map { width:100%; height:100%; }
  .err { color:#eee; font-family:system-ui,sans-serif; padding:1rem; }
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(async function () {
  const FILL = { galben:'#fdd835', portocaliu:'#fb8c00', rosu:'#e53935', alt:'#9e9e9e' };
  const EDGE = { galben:'#f9a825', portocaliu:'#ef6c00', rosu:'#b71c1c', alt:'#757575' };
  const params = new URLSearchParams(location.search);
  const src = params.get('src');
  if (!src) {
    document.body.innerHTML = '<div class="err">Lipsește parametrul src=</div>';
    return;
  }
  const url = src.startsWith('/') || src.startsWith('http')
    ? src
    : (location.pathname.replace(/[^/]+$/, '') + src);
  let geojson;
  try {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    geojson = await r.json();
  } catch (e) {
    document.body.innerHTML = '<div class="err">Nu pot încărca ' + url + ': ' + e + '</div>';
    return;
  }
  const map = L.map('map', { zoomControl: true }).setView([45.9, 25.0], 6);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OSM', maxZoom: 12
  }).addTo(map);
  const layer = L.geoJSON(geojson, {
    style: f => {
      const n = f.properties.culoareNume || 'alt';
      const sel = f.properties.isSelected || f.properties.isGalati;
      return {
        color: sel ? '#bf360c' : (EDGE[n] || '#f9a825'),
        weight: sel ? 2.5 : 0.6,
        fillColor: FILL[n] || '#fdd835',
        fillOpacity: sel ? 0.8 : 0.4,
      };
    },
    onEachFeature: (f, l) => {
      const p = f.properties || {};
      l.bindPopup((p.nume || p.cod || '') + ': ' + (p.culoareNume || ''));
    }
  }).addTo(map);
  try { map.fitBounds(layer.getBounds(), { padding: [16, 16] }); } catch (e) {}
})();
</script>
</body>
</html>
"""
