import type { StyleSpecification } from 'maplibre-gl';

const TOKENS = ['land', 'water', 'rail', 'road', 'label', 'halo'] as const;
type Palette = Record<(typeof TOKENS)[number], string>;

/** Reads the map's CSS tokens as real colours for MapLibre */
function palette(): Palette {
  const probe = document.body.appendChild(document.createElement('i'));
  const colours = TOKENS.map((token) => {
    probe.style.color = `var(--map-${token})`;
    return getComputedStyle(probe).color;
  });
  probe.remove();
  return Object.fromEntries(TOKENS.map((token, i) => [token, colours[i]])) as Palette;
}

const OSM = 'openmaptiles';

export function basemap(): StyleSpecification {
  const c = palette();
  return {
    version: 8,
    glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
    sources: {
      [OSM]: {
        type: 'vector',
        url: 'https://tiles.openfreemap.org/planet',
        attribution:
          '<a href="https://openfreemap.org">OpenFreeMap</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }
    },
    layers: [
      { id: 'land', type: 'background', paint: { 'background-color': c.land } },
      {
        id: 'water',
        type: 'fill',
        source: OSM,
        'source-layer': 'water',
        paint: { 'fill-color': c.water }
      },
      {
        id: 'roads',
        type: 'line',
        source: OSM,
        'source-layer': 'transportation',
        minzoom: 7,
        filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary']]],
        paint: { 'line-color': c.road, 'line-width': 1 }
      },
      {
        id: 'rail',
        type: 'line',
        source: OSM,
        'source-layer': 'transportation',
        filter: ['all', ['==', ['get', 'class'], 'rail'], ['!=', ['get', 'service'], 'yard']],
        paint: {
          'line-color': c.rail,
          'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.5, 10, 1.5]
        }
      },
      {
        id: 'places',
        type: 'symbol',
        source: OSM,
        'source-layer': 'place',
        filter: [
          'any',
          ['==', ['get', 'class'], 'city'],
          ['all', ['==', ['get', 'class'], 'town'], ['>=', ['zoom'], 8]]
        ],
        layout: {
          'text-field': ['coalesce', ['get', 'name:en'], ['get', 'name']],
          'text-font': ['Noto Sans Regular'],
          'text-size': ['match', ['get', 'class'], 'city', 12, 11],
          'text-max-width': 8
        },
        paint: { 'text-color': c.label, 'text-halo-color': c.halo, 'text-halo-width': 1.5 }
      }
    ]
  };
}
