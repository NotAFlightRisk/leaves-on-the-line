<script lang="ts">
  import 'maplibre-gl/dist/maplibre-gl.css';
  import worker from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
  import type { GeoJSONSource, Map as MapLibre } from 'maplibre-gl';
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

  const KINDS = {
    line: 'between these stations',
    dot: 'at the station',
    ring: 'on a line out of here'
  };

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
    import('maplibre-gl').then(
      ({ Map, NavigationControl, AttributionControl, Popup, setWorkerUrl }) => {
        if (!alive) return;
        setWorkerUrl(worker);
        let target: MapLibre;
        try {
          target = new Map({
            container,
            style: basemap(),
            bounds: [
              [-6.4, 49.9],
              [1.8, 58.7]
            ],
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
        target.addControl(new NavigationControl({ showCompass: false }), 'top-right');
        target.addControl(new AttributionControl({ compact: true }), 'bottom-right');
        container.querySelector('.maplibregl-ctrl-attrib')?.classList.add('maplibregl-compact');
        target.on('load', () => {
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
          for (const layer of ['chords', 'rings', 'dots']) {
            target.on('click', layer, (event) => {
              const props = event.features?.[0]?.properties;
              if (!props) return;
              const tip = document.createElement('div');
              tip.append(
                Object.assign(document.createElement('strong'), { textContent: props.name }),
                Object.assign(document.createElement('span'), {
                  textContent: ` ${minutes(props.value)} minutes ${KINDS[props.kind as keyof typeof KINDS]}`
                })
              );
              new Popup({ className: 'tip', maxWidth: '18rem' })
                .setLngLat(event.lngLat)
                .setDOMContent(tip)
                .addTo(target);
            });
            target.on('mouseenter', layer, () => (target.getCanvas().style.cursor = 'pointer'));
            target.on('mouseleave', layer, () => (target.getCanvas().style.cursor = ''));
          }
          map = target;
        });
      }
    );
    return () => {
      alive = false;
      map?.remove();
    };
  });
</script>

<div class="frame">
  <div class="map" bind:this={container}></div>
  {#if broken}
    <p class="broken">
      This browser can't draw the map, as it needs WebGL2. The table below has the same numbers.
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
    height: min(75dvh, 46rem);
    min-height: 26rem;
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

  .frame :global {
    .tip .maplibregl-popup-content {
      background: var(--panel-raised);
      color: var(--text);
      border: 1px solid var(--rule-strong);
      border-radius: var(--radius);
      font: inherit;
      font-size: var(--step--1);
      padding: var(--space-2) var(--space-3);
    }

    .tip .maplibregl-popup-tip {
      border-top-color: var(--rule-strong);
      border-bottom-color: var(--rule-strong);
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

    .maplibregl-ctrl-icon {
      filter: invert(1) brightness(0.85);
    }
  }
</style>
