<script lang="ts">
  import { getJson, type Place, type Series } from '#lib/data.ts';
  import { cause } from '#lib/causes.ts';
  import { dateLong, minutes } from '#lib/format.ts';
  import Columns from '#lib/components/Columns.svelte';
  import Meta from '#lib/components/Meta.svelte';

  let { data } = $props();

  const index = $derived(data.index);
  const trends = $derived(data.trends);
  const periods = $derived(index.periods);
  const lastFile = $derived(periods[index.last]);
  const label = (id: string) => index.groups.find((g) => g.id === id)?.label ?? id;

  let operator = $state('');
  let picked: Place | null = $state(null);
  let loading = $state(false);

  let asked = 0;

  async function pick() {
    const ask = ++asked;
    if (!operator) {
      picked = null;
      return;
    }
    loading = true;
    const found = await getJson<Place>(fetch, `/operator/${operator}.json`);
    if (ask !== asked) return;
    picked = found;
    loading = false;
  }

  const ours = (id: string): Series => (picked ? picked.minutes : index.network.minutes)[id] ?? [];
  const theirs = (id: string): Series | undefined =>
    (picked ? picked.orr : trends.orr)?.[id === 'autumn' ? '' : id];
  // one scale for every cause, so a small one never draws as big as a large one
  const top = $derived(
    Math.max(
      1,
      ...index.groups.flatMap((g) =>
        [ours(g.id), theirs(g.id) ?? []].flatMap((series) =>
          series.map((v, i) => (v ?? 0) / periods[i].days)
        )
      )
    )
  );
  const filed = $derived(periods.slice(0, index.last + 1));
  const people = $derived(trends.people.slice(0, index.last + 1));
  const peopleTop = $derived(Math.max(1, ...people.map((v, i) => (v ?? 0) / filed[i].days)));
  const topDay = $derived(trends.worst[0]);
</script>

<Meta
  title="Trends since 2018"
  description="Every cause of delay on Britain's railways, period by period since April 2018, network-wide and by operator, with the worst days and the storms."
/>

<div class="trends">
  <header>
    <h1>Every cause, period by period since 2018</h1>
    <p class="intro">
      Delay minutes a day in each four-week period. Our files run to {lastFile.label}; after that
      the dashed outlines are ORR's own Table 3184, which sorts causes into the same groups but
      can't split autumn out, counts incidents involving people and leaves out lines off Network
      Rail's track, so it's drawn apart and never joined on. Hatched bars were under 94% agreed when
      their file came out, and every cause shares one scale.
    </p>
    <div class="controls">
      <label>
        Whose trains
        <span class="select">
          <select bind:value={operator} onchange={pick}>
            <option value="">The whole network</option>
            {#each index.operators as op (op.id)}
              <option value={op.id}>{op.name}</option>
            {/each}
          </select>
        </span>
      </label>
      <a href="/trends.csv" rel="external" download>CSV</a>
      {#if loading}<span role="status">Loading...</span>{/if}
    </div>
  </header>

  <section class="grid" aria-label="Causes">
    {#each index.groups as group (group.id)}
      <Columns
        ours={ours(group.id)}
        theirs={theirs(group.id)}
        {periods}
        colour={cause(group.id)}
        label={group.label}
        {top}
      />
    {/each}
  </section>

  <section aria-labelledby="people">
    <h2 id="people">Incidents involving people</h2>
    <p class="intro">
      Fatalities, trespass, welfare concerns, police searches and ill or injured passengers, left
      out of every other figure on this site. They show here only as one network total a period, so
      nothing can point at a day or a place. ORR's table counts them inside its other causes, so
      there's nothing to show after our files end in {lastFile.label}.
    </p>
    <Columns
      ours={people}
      periods={filed}
      colour="var(--text-muted)"
      label="Network total"
      top={peopleTop}
    />
  </section>

  <section aria-labelledby="days">
    <h2 id="days">The worst days</h2>
    <p class="intro">
      Network totals only, the one place this site goes down to a day. The worst was {dateLong(
        topDay[0]
      )}, with
      {minutes(topDay[1])} delay minutes.
    </p>
    <div class="days">
      {#each [['All causes', trends.worst], ['Weather', trends.storms]] as const as [title, days] (title)}
        <table>
          <caption>{title}</caption>
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th scope="col" class="num">Minutes</th>
              <th scope="col">Biggest cause</th>
            </tr>
          </thead>
          <tbody>
            {#each days.slice(0, 12) as [day, total, by] (day)}
              {@const [top] = Object.entries(by).sort((a, b) => b[1] - a[1])}
              <tr>
                <td>{dateLong(day)}</td>
                <td class="num">{minutes(title === 'Weather' ? by.weather : total)}</td>
                <td><span class="chip" style:background={cause(top[0])}></span>{label(top[0])}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/each}
    </div>
  </section>
</div>

<style>
  .trends {
    display: grid;
    gap: var(--space-6);
  }

  header {
    display: grid;
    gap: var(--space-4);

    h1 {
      font-size: var(--step-3);
      letter-spacing: -0.02em;
    }
  }

  .intro {
    color: var(--text-muted);
    max-width: var(--measure);
  }

  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-4);

    label {
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
    }
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 20rem), 1fr));
    gap: var(--space-5) var(--space-6);
  }

  section {
    display: grid;
    gap: var(--space-3);

    h2 {
      font-size: var(--step-1);
    }
  }

  .days {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
    gap: var(--space-6);
  }

  table {
    width: 100%;
    font-size: var(--step--1);
  }

  caption {
    text-align: left;
    font-weight: 700;
    padding-bottom: var(--space-2);
  }

  th,
  td {
    padding: var(--space-1) var(--space-2);
    border-bottom: 1px solid var(--rule);
    text-align: left;
  }

  th {
    color: var(--text-faint);
    font-weight: 400;
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .chip {
    display: inline-block;
    width: 0.65rem;
    height: 0.65rem;
    margin-right: var(--space-2);
    border-radius: 2px;
  }
</style>
