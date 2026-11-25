<script lang="ts">
  import { untrack, type Snippet } from 'svelte';
  import type { Index, Place } from '#lib/data.ts';
  import { dateLong } from '#lib/format.ts';
  import Board from './Board.svelte';
  import Codes from './Codes.svelte';
  import History from './History.svelte';
  import InfoSign from './InfoSign.svelte';
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
  const path = $derived(`/${place.kind}/${place.id}`);
</script>

<article class="place">
  <header>
    <div class="name sign">
      <h1>{heading}</h1>
      {#if tags}<div class="tags">{@render tags()}</div>{/if}
    </div>
    <div class="strip">
      <PeriodPicker periods={index.periods} bind:at />
      <span class="downloads">
        Download these figures as
        <a href="{path}.csv" rel="external" download>CSV</a>
        or <a href="{path}.json" rel="external">JSON</a>
      </span>
    </div>
  </header>

  {#if at === index.last}
    <p class="stale">
      <strong>These figures stop at {dateLong(index.periods[index.last].end)}.</strong>
      {#if place.kind === 'operator'}
        That's the last month Network Rail made public in this detail. For newer monthly totals for {place.name},
        see the <a href="/trends">trends page</a>.
      {:else}
        That's the last month Network Rail made public {place.kind === 'station'
          ? 'station by station'
          : 'route by route'}. The <a href="/">homepage</a> has the latest month for the whole network.
      {/if}
    </p>
  {/if}

  <InfoSign breakdown={place} groups={index.groups} periods={index.periods} {at} {where} />

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
        There's no comparison with other years here. With under 100 minutes of delay a month, the
        changes would mostly be chance.
      </p>
    {/if}
  </section>

  <section aria-labelledby="history">
    <h2 id="history">Month by month</h2>
    <History breakdown={place} groups={index.groups} periods={index.periods} bind:at name={where} />
  </section>

  {@render children?.()}

  <section aria-labelledby="codes">
    <h2 id="codes">The codes behind it</h2>
    <Codes latest={place.codes.latest} all={place.codes.all} period="the latest month" />
  </section>

  <aside class="counts">
    <h2>What this counts</h2>
    <p>{counts}</p>
    <p>
      Cancelled trains are counted as trains, not minutes. Delay involving people, like trespass, is
      left out. <a href="/method">Read how it's worked out</a>.
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
  }

  .name {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--space-3) var(--space-5);
    padding: var(--space-5) var(--space-5) var(--space-4);
    border-radius: var(--radius) var(--radius) 0 0;
    border-bottom: 10px solid var(--edge);

    h1 {
      font-size: clamp(2.6rem, 7vw, 5.5rem);
      line-height: 0.95;
      letter-spacing: -0.025em;
    }
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3);
  }

  .stale {
    margin-top: calc(-1 * var(--space-5));
    padding: var(--space-3) var(--space-5);
    background: var(--edge);
    color: var(--sign);
    border-radius: var(--radius);
    max-width: none;

    a {
      color: var(--sign);
    }
  }

  .strip {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3) var(--space-5);
    padding: var(--space-3) var(--space-5);
    background: var(--panel);
    border-radius: 0 0 var(--radius) var(--radius);
  }

  .downloads {
    font-size: var(--step--1);
    color: var(--text-muted);

    a {
      font-weight: 700;
    }
  }

  section {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }

  h2 {
    font-size: var(--step-2);
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

  @media (max-width: 30rem) {
    .name,
    .strip,
    .stale {
      padding-inline: var(--space-4);
    }
  }
</style>
