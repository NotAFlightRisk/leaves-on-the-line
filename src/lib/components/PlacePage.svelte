<script lang="ts">
  import { untrack, type Snippet } from 'svelte';
  import type { Index, Place } from '#lib/data.ts';
  import { knockOnLine, summarise, totalAt } from '#lib/compare.ts';
  import { dateShort, percent } from '#lib/format.ts';
  import Board from './Board.svelte';
  import Codes from './Codes.svelte';
  import Figure from './Figure.svelte';
  import History from './History.svelte';
  import PeriodPicker from './PeriodPicker.svelte';

  let {
    place,
    index,
    where,
    heading = place.name,
    tags,
    counts,
    children
  }: {
    place: Place;
    heading?: string;
    index: Index;
    where: string;
    tags?: Snippet;
    counts: string;
    children?: Snippet;
  } = $props();

  let at = $state(untrack(() => index.last));
  const period = $derived(index.periods[at]);
  const total = $derived(totalAt(place, at));
  const agreed = $derived(total ? 1 - (place.unagreed[at] ?? 0) / total : 1);
  const path = $derived(`/${place.kind}/${place.id}`);
</script>

<article class="place">
  <header>
    <h1>{heading}</h1>
    <div class="tags">
      {@render tags?.()}
      <PeriodPicker periods={index.periods} bind:at />
      <span class="downloads">
        <a href="{path}.csv" rel="external" download>CSV</a>
        <a href="{path}.json" rel="external">JSON</a>
      </span>
    </div>
  </header>

  <section class="lead" aria-label="Summary">
    <Figure value={total} unit="delay minutes" />
    <p class="sentence">{summarise(place, index.groups, period, at, where)}</p>
    <p class="aside">
      {knockOnLine(place, at)}
      {percent(agreed)} of them were agreed between Network Rail and the operators when the file came
      out on {dateShort(period.released ?? period.end)}{agreed < 0.94
        ? ', so they may still move'
        : ''}.
    </p>
  </section>

  <section aria-labelledby="causes">
    <h2 id="causes">By cause</h2>
    <Board
      breakdown={place}
      network={index.network}
      groups={index.groups}
      periods={index.periods}
      {at}
      compare={!place.quiet}
    />
    {#if place.quiet}
      <p class="note">
        Quiet enough here (under 100 delay minutes a period on average) that comparing years would
        mostly be noise, so there's no comparison.
      </p>
    {/if}
  </section>

  <section aria-labelledby="history">
    <h2 id="history">Period by period</h2>
    <History breakdown={place} groups={index.groups} periods={index.periods} bind:at name={where} />
  </section>

  {@render children?.()}

  <section aria-labelledby="codes">
    <h2 id="codes">The codes behind it</h2>
    <Codes
      latest={place.codes.latest}
      all={place.codes.all}
      period={index.periods[index.last].label}
    />
  </section>

  <aside class="counts">
    <h2>What this counts</h2>
    <p>{counts}</p>
    <p>
      Delay minutes are delay events on passenger trains, as ORR counts them. Cancelled trains are
      counted as trains, not minutes. Incidents involving people are left out of everything below a
      network total. <a href="/method">More on the method</a>.
    </p>
  </aside>
</article>

<style>
  .place {
    display: grid;
    gap: var(--space-7);
  }

  header {
    display: grid;
    gap: var(--space-4);

    h1 {
      font-size: var(--step-3);
      letter-spacing: -0.02em;
    }
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3);
  }

  .downloads {
    display: inline-flex;
    gap: var(--space-3);
    font-size: var(--step--1);
  }

  .lead {
    display: grid;
    gap: var(--space-3);
    padding: var(--space-5) var(--space-5) var(--space-6);
    background: var(--panel);
    border: 1px solid var(--rule);
    border-radius: var(--radius);
  }

  .sentence {
    font-size: var(--step-1);
    max-width: var(--measure);
  }

  .aside {
    color: var(--text-muted);
    max-width: var(--measure);
  }

  section {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }

  h2 {
    font-size: var(--step-1);
  }

  .note {
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: var(--measure);
  }

  .counts {
    display: grid;
    gap: var(--space-3);
    padding-top: var(--space-5);
    border-top: 1px solid var(--rule);
    color: var(--text-muted);

    p {
      max-width: var(--measure);
    }
  }
</style>
