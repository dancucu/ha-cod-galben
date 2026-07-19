"""Self-contained GIS map viewer (no CDN) for Cod Galben.

Usage: /local/cod_galben/map.html?src=/local/cod_galben/gis_4185.json
Prefers companion .svg if present; otherwise renders GeoJSON client-side.
"""

from __future__ import annotations

MAP_HTML = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cod Galben — hartă GIS</title>
<style>
  html, body { margin:0; height:100%; background:#111; }
  #wrap { width:100%; height:100%; display:flex; align-items:center; justify-content:center; }
  img, svg { width:100%; height:100%; object-fit:contain; display:block; }
  .err { color:#eee; font-family:system-ui,sans-serif; padding:1rem; }
</style>
</head>
<body>
<div id="wrap"></div>
<script>
(async function () {
  const FILL = { galben:'#fdd835', portocaliu:'#fb8c00', rosu:'#e53935', alt:'#9e9e9e' };
  const EDGE = { galben:'#f9a825', portocaliu:'#ef6c00', rosu:'#b71c1c', alt:'#757575' };
  const wrap = document.getElementById('wrap');
  const params = new URLSearchParams(location.search);
  let src = params.get('src');
  if (!src) {
    wrap.innerHTML = '<div class="err">Lipsește parametrul src=</div>';
    return;
  }
  if (!(src.startsWith('/') || src.startsWith('http'))) {
    src = location.pathname.replace(/[^/]+$/, '') + src;
  }
  // Prefer pre-rendered SVG (same basename)
  const svgUrl = src.replace(/\\.json(\\?.*)?$/i, '.svg$1');
  if (svgUrl !== src) {
    try {
      const r = await fetch(svgUrl, { cache: 'no-store' });
      if (r.ok) {
        const blob = await r.blob();
        const img = document.createElement('img');
        img.alt = 'Hartă GIS';
        img.src = URL.createObjectURL(blob);
        wrap.appendChild(img);
        return;
      }
    } catch (e) {}
  }
  let geojson;
  try {
    const r = await fetch(src, { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    geojson = await r.json();
  } catch (e) {
    wrap.innerHTML = '<div class="err">Nu pot încărca ' + src + ': ' + e + '</div>';
    return;
  }
  const W = 720, H = 480, PAD = 12;
  const features = geojson.features || [];
  const pts = [];
  for (const f of features) {
    const g = f.geometry || {};
    const rings = g.type === 'Polygon' ? (g.coordinates || [])
      : g.type === 'MultiPolygon' ? (g.coordinates || []).flat()
      : [];
    for (const ring of rings) for (const c of ring) pts.push(c);
  }
  if (!pts.length) {
    wrap.innerHTML = '<div class="err">Fără poligoane</div>';
    return;
  }
  let minLon=pts[0][0], maxLon=pts[0][0], minLat=pts[0][1], maxLat=pts[0][1];
  for (const [lon,lat] of pts) {
    if (lon<minLon) minLon=lon; if (lon>maxLon) maxLon=lon;
    if (lat<minLat) minLat=lat; if (lat>maxLat) maxLat=lat;
  }
  const spanLon = Math.max(maxLon-minLon, 1e-6);
  const spanLat = Math.max(maxLat-minLat, 1e-6);
  const uw = W-2*PAD, uh = H-2*PAD;
  const scale = Math.min(uw/spanLon, uh/spanLat);
  const ox = PAD + (uw - spanLon*scale)/2;
  const oy = PAD + (uh - spanLat*scale)/2;
  const proj = (lon, lat) => [ox + (lon-minLon)*scale, oy + (maxLat-lat)*scale];
  const sorted = features.slice().sort((a,b) => {
    const sa = (a.properties&& (a.properties.isSelected||a.properties.isGalati)) ? 1 : 0;
    const sb = (b.properties&& (b.properties.isSelected||b.properties.isGalati)) ? 1 : 0;
    return sa - sb;
  });
  let paths = '';
  for (const f of sorted) {
    const p = f.properties || {};
    const n = p.culoareNume || 'alt';
    const sel = p.isSelected || p.isGalati;
    const fill = FILL[n] || FILL.alt;
    const stroke = sel ? '#bf360c' : (EDGE[n] || EDGE.alt);
    const sw = sel ? 2.5 : 0.6;
    const op = sel ? 0.85 : 0.45;
    const g = f.geometry || {};
    const rings = g.type === 'Polygon' ? (g.coordinates || [])
      : g.type === 'MultiPolygon' ? (g.coordinates || []).flat()
      : [];
    for (const ring of rings) {
      if (!ring || ring.length < 3) continue;
      const d = ring.map(([lon,lat]) => proj(lon,lat).map(x => x.toFixed(2)).join(',')).join(' ');
      paths += `<polygon points="${d}" fill="${fill}" fill-opacity="${op}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    }
  }
  wrap.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="100%" height="100%"><rect width="100%" height="100%" fill="#111"/>${paths}</svg>`;
})();
</script>
</body>
</html>
"""
