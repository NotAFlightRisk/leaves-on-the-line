<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { getJson, type Feature, type MapPeriod } from '#lib/data.ts';
  import { cause } from '#lib/causes.ts';
  import { minutes, percent, periodName } from '#lib/format.ts';
  import Meta from '#lib/components/Meta.svelte';
  import RailMap from '#lib/components/RailMap.svelte';

  let { data } = $props();

  const index = $derived(data.index);
  const choices = $derived(index.periods.flatMap((p, i) => (p.file ? [i] : [])));
  const yearOf = (i: number) => index.periods[i].id.slice(0, 7);

  // the last whole year, so the first look has every season in it
  const inLastWhole = untrack(() => {
    const { periods, last } = data.index;
    const year = periods[Math.max(0, last - 13)].id.slice(0, 7);
    return periods.flatMap((p, i) => (p.file && p.id.startsWith(year) ? [i] : []));
  });

  let group = $state('');
  let from = $state(inLastWhole[0]);
  let to = $state(inLastWhole[inLastWhole.length - 1]);
  let features: Feature[] = $state([]);
  let loaded: MapPeriod[] = $state([]);
  let loading = $state(true);

  const files = new Map<string, Promise<MapPeriod>>();
  const file = (name: string) => {
    if (!files.has(name)) files.set(name, getJson<MapPeriod>(fetch, `/data/map/${name}.json`));
    return files.get(name)!;
  };

  /** Whole years in the range come as one file, the ragged ends a period at a time */
  function needed(a: number, b: number) {
    const inRange = choices.filter((i) => i >= a && i <= b);
    const years = new Set(inRange.map(yearOf));
    return [...years].flatMap((year) => {
      const all = choices.filter((i) => yearOf(i) === year);
      const whole = all.every((i) => i >= a && i <= b);
      return whole ? [year] : all.filter((i) => i >= a && i <= b).map((i) => index.periods[i].id);
    });
  }

  let asked = 0;

  $effect(() => {
    const names = needed(Math.min(from, to), Math.max(from, to));
    const ask = ++asked;
    loading = true;
    Promise.all(names.map(file)).then((parts) => {
      if (ask !== asked) return;
      loaded = parts;
      loading = false;
    });
  });

  onMount(async () => {
    features = await getJson<Feature[]>(fetch, '/data/map/features.json');
  });

  const groupIndex = $derived(index.groups.findIndex((g) => g.id === group));
  const values = $derived.by(() => {
    const out = new Map<number, number>();
    for (const part of loaded) {
      for (const [f, g, m] of part.m) {
        if (groupIndex < 0 || g === groupIndex) out.set(f, (out.get(f) ?? 0) + m);
      }
    }
    return out;
  });
  const drawn = $derived([...values.values()].reduce((a, b) => a + b, 0));
  const off = $derived(
    loaded.reduce(
      (sum, part) =>
        sum +
        Object.entries(part.off).reduce((s, [g, m]) => s + (!group || g === group ? m : 0), 0),
      0
    )
  );
  const worst = $derived(
    features.length ? [...values].sort((a, b) => b[1] - a[1]).slice(0, 15) : []
  );
  const tint = $derived(group ? cause(group) : 'var(--figure)');
  const KINDS = { line: 'between stations', dot: 'at the station', ring: 'on a line out of here' };
</script>

<Meta
  title="The map: where each cause of delay starts"
  description="A map of where Britain's rail delays start, by cause and period since 2018: leaf-fall, flooding, signal failures and cable theft hotspots, from Network Rail's own records."
/>

<div class="page">
  <header>
    <h1>Where each cause starts</h1>
    <p class="intro">
      Each line is a section of track between two stations where incidents started, thicker for more
      delay, counting all the knock-on it caused anywhere. Sections are drawn straight from station
      to station (13.7 km at the middle, up to 52), so they cut corners and the map stops zooming in
      at about town level.
    </p>
  </header>

  <form class="controls" aria-label="What to show" onsubmit={(e) => e.preventDefault()}>
    <label>
      Cause
      <span class="select">
        <select bind:value={group}>
          <option value="">All causes</option>
          {#each index.groups as g (g.id)}
            <option value={g.id}>{g.label}</option>
          {/each}
        </select>
      </span>
    </label>
    <label>
      From
      <span class="select">
        <select bind:value={from}>
          {#each choices as i (i)}<option value={i}>{periodName(index.periods[i])}</option>{/each}
        </select>
      </span>
    </label>
    <label>
      To
      <span class="select">
        <select bind:value={to}>
          {#each choices as i (i)}<option value={i}>{periodName(index.periods[i])}</option>{/each}
        </select>
      </span>
    </label>
    <p class="status" role="status">
      {#if loading}Loading...{:else}{minutes(drawn)} minutes drawn{/if}
    </p>
  </form>

  <div class="split">
    <div class="mapped">
      <RailMap {features} {values} colour={tint} />

      <div class="key">
        <span>
          <svg viewBox="0 0 24 8" aria-hidden="true">
            <line x1="2" y1="4" x2="22" y2="4" style:stroke={tint} />
          </svg> Between two stations
        </span>
        <span>
          <svg viewBox="0 0 12 12" aria-hidden="true">
            <circle cx="6" cy="6" r="4" style:fill={tint} />
          </svg> At a station
        </span>
        <span>
          <svg viewBox="0 0 12 12" aria-hidden="true">
            <circle cx="6" cy="6" r="4" class="ring" style:stroke={tint} />
          </svg> On a line out of here
        </span>
        {#if drawn + off > 0}
          <span class="off">
            {percent(off / (drawn + off))} of this delay started at junctions and sidings with no station
            at either end, so it isn't drawn.
          </span>
        {/if}
      </div>
    </div>

    <section aria-labelledby="worst">
      <h2 id="worst">The worst of it</h2>
      <table>
        <thead>
          <tr>
            <th scope="col">Where</th>
            <th scope="col">Kind</th>
            <th scope="col" class="num">Minutes</th>
          </tr>
        </thead>
        <tbody>
          {#each worst as [f, value] (f)}
            <tr>
              <td>{features[f][1]}</td>
              <td class="muted">{KINDS[features[f][0]]}</td>
              <td class="num">{minutes(value)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>
  </div>
</div>

<style>
  .page {
    display: grid;
    gap: var(--space-5);
  }

  header {
    display: grid;
    gap: var(--space-3);

    h1 {
      font-size: var(--step-3);
    }
  }

  .intro {
    color: var(--text-muted);
    max-width: var(--measure);
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: end;
    gap: var(--space-3) var(--space-5);

    label {
      display: grid;
      gap: var(--space-1);
      font-size: var(--step--1);
      color: var(--text-muted);
    }
  }

  .status {
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
    padding-bottom: var(--space-2);
  }

  .split {
    display: grid;
    gap: var(--space-6);
    align-items: start;

    @media (min-width: 64rem) {
      grid-template-columns: minmax(0, 1.25fr) minmax(18rem, 1fr);
    }
  }

  .mapped {
    display: grid;
    gap: var(--space-3);
    min-width: 0;
  }

  .key {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2) var(--space-5);
    font-size: var(--step--1);
    color: var(--text-muted);

    span {
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
    }

    svg {
      width: 1.5rem;
      height: 0.75rem;
      stroke-width: 2.5;
      fill: none;
      stroke-linecap: round;
    }

    .ring {
      fill: none;
      stroke-width: 1.5;
    }

    .off {
      flex-basis: 100%;
    }
  }

  section {
    display: grid;
    gap: var(--space-3);

    h2 {
      font-size: var(--step-1);
    }
  }

  table {
    width: 100%;
    font-size: var(--step--1);
  }

  th,
  td {
    padding: var(--space-2);
    border-bottom: 1px solid var(--rule);
    text-align: left;
  }

  th {
    color: var(--text-faint);
    font-weight: 400;
  }

  .muted {
    color: var(--text-muted);
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
</style>
