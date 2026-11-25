<script lang="ts">
  import { cause } from '#lib/causes.ts';
  import { share, summarise, totalAt } from '#lib/compare.ts';
  import { dateLong, minutes, percent } from '#lib/format.ts';
  import Figure from '#lib/components/Figure.svelte';
  import Meta from '#lib/components/Meta.svelte';

  let { data } = $props();

  const index = $derived(data.index);
  const at = $derived(index.last);
  const period = $derived(index.periods[at]);
  const network = $derived(index.network);
  const total = $derived(totalAt(network, at));
  const causes = $derived(
    index.groups
      .map((g) => ({ g, value: network.minutes[g.id]?.[at] ?? 0 }))
      .sort((a, b) => b.value - a.value)
  );
</script>

<Meta
  title="Leaves on the Line"
  description="Why Britain's trains were late, cause by cause, for every station, route and operator since 2018, from Network Rail's own delay records."
/>

<div class="home">
  <section class="lead" aria-labelledby="title">
    <h1 id="title">Why Britain's trains were late, cause by cause</h1>
    <p class="intro">
      Network Rail puts a cause on every minute of delay, from signal failures to swans on the line.
      This is all of it since April 2018, for every station, route and operator.
    </p>
  </section>

  <section class="board" aria-labelledby="latest">
    <h2 id="latest">The four weeks to {dateLong(period.end)}</h2>
    <Figure value={total} unit="delay minutes on Britain's passenger trains" />
    <p class="sentence">{summarise(network, index.groups, period, at, 'across the network')}</p>
    <ol class="causes">
      {#each causes as { g, value } (g.id)}
        <li>
          <span
            class="bar"
            style:width="{share(value, causes[0].value) * 100}%"
            style:background={cause(g.id)}
          ></span>
          <span class="label">{g.label}</span>
          <span class="value">{minutes(value)} <span>{percent(share(value, total))}</span></span>
        </li>
      {/each}
    </ol>
    <p class="stale">
      That's the newest period Network Rail has published openly. Later ones sit behind the Rail
      Data Marketplace, so the <a href="/trends">trends</a> carry on from ORR's own tables.
    </p>
  </section>

  <section class="ways" aria-label="Ways in">
    <div>
      <h2>Your station</h2>
      <p>
        Use the search at the top, or browse <a href="/stations">
          all {minutes(index.stations)} stations
        </a>.
      </p>
    </div>
    <div>
      <h2>Routes</h2>
      <ul>
        {#each index.routes as route (route.id)}
          <li><a href="/route/{route.id}">{route.name}</a></li>
        {/each}
      </ul>
    </div>
    <div>
      <h2>Operators</h2>
      <ul>
        {#each index.operators as op (op.id)}
          <li><a href="/operator/{op.id}">{op.name}</a></li>
        {/each}
      </ul>
    </div>
    <div>
      <h2>The rest</h2>
      <ul>
        <li><a href="/map">The map</a>, where each cause starts</li>
        <li><a href="/trends">Trends</a> since 2018, storms and all</li>
        <li><a href="/odd">The odd ones</a>: swans, cows and balloons</li>
        <li><a href="/method">How it's worked out</a></li>
      </ul>
    </div>
  </section>
</div>

<style>
  .home {
    display: grid;
    gap: var(--space-7);
  }

  .lead {
    display: grid;
    gap: var(--space-4);

    h1 {
      font-size: var(--step-3);
      letter-spacing: -0.02em;
      max-width: 20ch;
    }
  }

  .intro {
    font-size: var(--step-1);
    color: var(--text-muted);
    max-width: var(--measure);
  }

  .board {
    display: grid;
    gap: var(--space-4);
    padding: var(--space-5) var(--space-5) var(--space-6);
    background: var(--panel);
    border: 1px solid var(--rule);
    border-radius: var(--radius);

    h2 {
      font-size: var(--step-0);
      color: var(--text-muted);
      font-weight: 400;
    }
  }

  .sentence {
    font-size: var(--step-1);
    max-width: var(--measure);
  }

  .causes {
    list-style: none;
    margin: var(--space-2) 0 0;
    padding: 0;
    display: grid;
    gap: var(--space-2);

    li {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 14rem 8rem;
      align-items: center;
      gap: var(--space-4);
      font-variant-numeric: tabular-nums;
    }

    .bar {
      grid-column: 1;
      grid-row: 1;
      height: 0.6rem;
      border-radius: 1px;
      min-width: 2px;
    }

    .label {
      grid-column: 2;
    }

    .value {
      grid-column: 3;
      text-align: right;
      font-weight: 700;

      span {
        display: inline-block;
        min-width: 3.5ch;
        font-weight: 400;
        color: var(--text-muted);
      }
    }
  }

  .stale {
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: var(--measure);
  }

  .ways {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
    gap: var(--space-6);

    h2 {
      font-size: var(--step-1);
      margin-bottom: var(--space-3);
    }

    ul {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: var(--space-1);
    }
  }

  @media (max-width: 40rem) {
    .causes li {
      grid-template-columns: minmax(0, 1fr) auto;

      .bar {
        grid-column: 1 / -1;
        grid-row: 2;
      }

      .label {
        grid-column: 1;
      }

      .value {
        grid-column: 2;
      }
    }
  }
</style>
