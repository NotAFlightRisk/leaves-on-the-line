<script lang="ts">
  import 'maplibre-gl/dist/maplibre-gl.css';
  import worker from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
  import type { GeoJSONSource, Map as MapLibre, MapLayerMouseEvent } from 'maplibre-gl';
  import { onMount } from 'svelte';
  import type { Feature } from '#lib/data.ts';
  import { minutes } from '#lib/format.ts';
  import { basemap } from '#lib/map/style.ts';

  let {
    features,
    values,
    colour
  }: { features: Feature[]; values: Map<number, number>; colour: string } = $props();

  let container: HTMLDivElement;
  let map: MapLibre | undefined = $state();
  let broken = $state(false);
  let bare = $state(false);

  const BRITAIN: [[number, number], [number, number]] = [
    [-6.4, 49.9],
    [1.8, 58.7]
  ];
  const KINDS = {
    line: 'between these stations',
    dot: 'at the station',
    ring: 'on a line out of here'
  };
  const LAYERS = ['chords', 'rings', 'dots'];

  function geojson() {
    const top = Math.max(1, ...values.values());
    return {
      type: 'FeatureCollection' as const,
      features: [...values].map(([i, value]) => {
        const [kind, name, ...c] = features[i];
        const geometry =
          kind === 'line'
            ? { type: 'LineString' as const, coordinates: [c.slice(0, 2), c.slice(2, 4)] }
            : { type: 'Point' as const, coordinates: c.slice(0, 2) };
        return {
          type: 'Feature' as const,
          geometry,
          properties: { kind, name, value, size: Math.sqrt(value / top) }
        };
      })
    };
  }

  function resolved() {
    const probe = document.body.appendChild(document.createElement('i'));
    probe.style.color = colour;
    const out = getComputedStyle(probe).color;
    probe.remove();
    return out;
  }

  $effect(() => {
    const source = map?.getSource<GeoJSONSource>('delay');
    if (!map || !source) return;
    source.setData(geojson());
    const tint = resolved();
    map.setPaintProperty('chords', 'line-color', tint);
    map.setPaintProperty('dots', 'circle-color', tint);
    map.setPaintProperty('rings', 'circle-stroke-color', tint);
  });

  onMount(() => {
    let alive = true;
    // `map` is only set once the layers are in, so this is what an early exit cleans up
    let made: MapLibre | undefined;
    import('maplibre-gl').then(
      ({ Map, NavigationControl, AttributionControl, Popup, setWorkerUrl }) => {
        if (!alive) return;
        setWorkerUrl(worker);
        let target: MapLibre;
        try {
          target = new Map({
            container,
            style: basemap(),
            bounds: BRITAIN,
            fitBoundsOptions: { padding: 16 },
            minZoom: 4.5,
            maxZoom: 10,
            maxBounds: [
              [-11, 49],
              [4, 61.5]
            ],
            attributionControl: false
          });
        } catch {
          broken = true;
          return;
        }
        made = target;
        target.addControl(new NavigationControl({ showCompass: false }), 'top-right');
        target.addControl(new AttributionControl({ compact: true }), 'bottom-right');
        container.querySelector('.maplibregl-ctrl-attrib')?.classList.add('maplibregl-compact');
        // the background is OpenFreeMap's, and the delay still draws without it
        target.on('error', (event) => {
          if (/openfreemap/i.test(String(event.error?.message ?? ''))) bare = true;
        });
        target.on('load', () => {
          target.resize();
          target.fitBounds(BRITAIN, { padding: 16, animate: false });
        });
        target.once('style.load', () => {
          const tint = resolved();
          target.addSource('delay', { type: 'geojson', data: geojson() });
          target.addLayer({
            id: 'chords',
            type: 'line',
            source: 'delay',
            filter: ['==', ['get', 'kind'], 'line'],
            layout: { 'line-cap': 'round' },
            paint: {
              'line-color': tint,
              'line-width': ['+', 0.6, ['*', 7, ['get', 'size']]],
              'line-opacity': ['+', 0.35, ['*', 0.6, ['get', 'size']]]
            }
          });
          target.addLayer({
            id: 'rings',
            type: 'circle',
            source: 'delay',
            filter: ['==', ['get', 'kind'], 'ring'],
            paint: {
              'circle-radius': ['+', 2.5, ['*', 12, ['get', 'size']]],
              'circle-color': 'rgba(0,0,0,0)',
              'circle-stroke-width': 1.5,
              'circle-stroke-color': tint
            }
          });
          target.addLayer({
            id: 'dots',
            type: 'circle',
            source: 'delay',
            filter: ['==', ['get', 'kind'], 'dot'],
            paint: {
              'circle-radius': ['+', 2, ['*', 12, ['get', 'size']]],
              'circle-color': tint,
              'circle-opacity': 0.85
            }
          });

          const popup = new Popup({
            className: 'tip',
            maxWidth: '18rem',
            closeButton: false,
            closeOnClick: false,
            offset: 12
          });
          const tipLine = (text: string, className = '') =>
            Object.assign(document.createElement('span'), { className, textContent: text });
          const describe = (event: MapLayerMouseEvent) => {
            const props = event.features?.[0]?.properties;
            if (!props) return;
            const tip = document.createElement('div');
            tip.append(
              tipLine(String(props.name), 'tip-when'),
              tipLine(`${minutes(Number(props.value))} minutes of delay`, 'tip-main'),
              tipLine(`From incidents ${KINDS[props.kind as keyof typeof KINDS]}.`)
            );
            popup.setLngLat(event.lngLat).setDOMContent(tip).addTo(target);
          };
          for (const layer of LAYERS) {
            target.on('mousemove', layer, (event) => {
              target.getCanvas().style.cursor = 'pointer';
              describe(event);
            });
            target.on('click', layer, describe);
            target.on('mouseleave', layer, () => {
              target.getCanvas().style.cursor = '';
              popup.remove();
            });
          }
          // touch has no mouseleave, so a tap away from the delay closes the tip
          target.on('click', (event) => {
            if (!target.queryRenderedFeatures(event.point, { layers: LAYERS }).length)
              popup.remove();
          });
          map = target;
        });
      }
    );
    return () => {
      alive = false;
      made?.remove();
    };
  });
</script>

<div class="frame">
  <div class="map" bind:this={container}></div>
  {#if bare && !broken}
    <p class="bare" role="status">
      The background map didn't load, so the delay is drawn on its own. Try reloading the page.
    </p>
  {/if}
  {#if broken}
    <p class="broken">
      This browser can't draw the map, because it needs WebGL2. The table has the same numbers.
    </p>
  {/if}
</div>

<style>
  .frame {
    position: relative;
    border: 1px solid var(--rule);
    border-radius: var(--radius);
    overflow: hidden;
    background: var(--map-land);
  }

  .map {
    height: min(80dvh, 50rem);
    min-height: 28rem;
  }

  .broken {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    padding: var(--space-6);
    text-align: center;
    color: var(--text-muted);
  }

  .bare {
    position: absolute;
    left: var(--space-3);
    right: var(--space-3);
    top: var(--space-3);
    padding: var(--space-2) var(--space-3);
    background: var(--edge);
    color: var(--sign);
    border-radius: var(--radius);
    font-size: var(--step--1);
    font-weight: 600;
    z-index: 2;
  }

  .frame :global {
    .tip {
      pointer-events: none;
    }

    .tip .maplibregl-popup-content {
      display: grid;
      background: var(--sign);
      color: var(--on-sign);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      font: inherit;
      font-size: 0.875rem;
      line-height: 1.4;
      padding: var(--space-3) var(--space-4);
    }

    .tip .maplibregl-popup-tip {
      border-top-color: var(--sign);
      border-bottom-color: var(--sign);
    }

    .tip .maplibregl-popup-close-button {
      color: var(--text-muted);
    }

    .maplibregl-ctrl-group,
    .maplibregl-ctrl-attrib {
      background: var(--panel-raised);
      color: var(--text-muted);
    }

    .maplibregl-ctrl-attrib a {
      color: var(--link);
    }

    .maplibregl-ctrl-group button + button {
      border-top-color: var(--rule-strong);
    }

    .maplibregl-ctrl-group {
      background: var(--panel);
      box-shadow: 0 0 0 2px var(--sign);
    }
  }
</style>
