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
<title>Cod Galben — hartă GIS v1.3.10</title>
<link rel="stylesheet" href="leaflet.css"/>
<style>
  html, body { margin:0; height:100%; background:#fff; }
  #map { width:100%; height:100%; }
  .err { color:#333; font-family:system-ui,sans-serif; padding:1rem; }
  /* fundal default Leaflet (ca pe leafletjs.com) */
  .leaflet-container { background:#ddd; font: 12px/1.5 "Helvetica Neue", Arial, Helvetica, sans-serif; }
</style>
</head>
<body>
<div id="map"></div>
<script src="leaflet.js"></script>
<script>
(async function () {
  const FILL = { galben:'#ffde07', portocaliu:'#f09035', rosu:'#ea3323', alt:'#cfd8dc' };
  const EDGE = { galben:'#c9b000', portocaliu:'#c56e18', rosu:'#c62828', alt:'#90a4ae' };
  const FILL_OPACITY = 0.45;
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

  // Ca pe https://leafletjs.com/ — map + tile layer din ?tiles=osm|topo
  const map = L.map('map', {
    zoomControl: true,
    attributionControl: true,
    maxBounds: ROMANIA.pad(0.15),
    maxBoundsViscosity: 0.6,
  });

  const tiles = (params.get('tiles') || 'osm').toLowerCase();
  if (tiles === 'topo') {
    L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 17,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)',
    }).addTo(map);
  } else {
    // default: OSM — același URL ca pe leafletjs.com
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
  }

  map.createPane('romaniaBorder');
  map.getPane('romaniaBorder').style.zIndex = 450;
  map.getPane('romaniaBorder').style.pointerEvents = 'none';

  try {
    const rr = await fetch('romania.geojson', { cache: 'force-cache' });
    if (rr.ok) {
      const ro = await rr.json();
      L.geoJSON(ro, {
        pane: 'romaniaBorder',
        style: {
          color: '#4a4a4a',
          weight: 1.25,
          opacity: 0.45,
          fill: false,
          lineJoin: 'round',
          lineCap: 'round',
        },
      }).addTo(map);
    }
  } catch (_) { /* contur opțional */ }

  const feats = geojson.features || [];
  const base = { type:'FeatureCollection', features: feats.filter(f => !(f.properties||{}).overlay && (f.properties||{}).zoneType !== 'overlay') };
  const overs = { type:'FeatureCollection', features: feats.filter(f => (f.properties||{}).overlay || (f.properties||{}).zoneType === 'overlay') };

  function styleFeature(f) {
    const p = f.properties || {};
    const n = p.culoareNume || 'alt';
    const sel = p.isSelected || p.isGalati;
    return {
      color: sel ? '#bf360c' : (EDGE[n] || EDGE.alt),
      weight: sel ? 1.2 : 0.5,
      opacity: sel ? 0.55 : 0.45,
      fillColor: FILL[n] || FILL.alt,
      fillOpacity: FILL_OPACITY,
    };
  }

  function bindFeature(f, l) {
    const p = f.properties || {};
    const label = (p.nume || p.cod || '') + (p.culoareNume ? (': ' + p.culoareNume) : '');
    l.bindPopup(label);
    if (!p.overlay && p.zoneType !== 'overlay' && (p.cod_base || p.cod)) {
      l.bindTooltip(p.cod_base || String(p.cod).split('_')[0], {
        permanent: false, direction: 'center', className: 'county-tip'
      });
    }
  }

  L.geoJSON(base, { style: styleFeature, onEachFeature: bindFeature }).addTo(map);
  L.geoJSON(overs, { style: styleFeature, onEachFeature: bindFeature }).addTo(map);

  map.fitBounds(ROMANIA, { padding: [8, 8], maxZoom: 7 });
  setTimeout(() => map.invalidateSize(), 50);
})();
</script>
</body>
</html>
"""
