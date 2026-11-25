<script lang="ts">
  import { minutes } from '#lib/format.ts';
  import Meta from '#lib/components/Meta.svelte';

  let { data } = $props();

  const plurals: Record<string, string> = {
    swan: 'Swans',
    deer: 'Deer',
    cow: 'Cows and cattle',
    sheep: 'Sheep',
    horse: 'Horses',
    badger: 'Badgers',
    fox: 'Foxes',
    dog: 'Dogs',
    bird: 'Birds',
    tree: 'Trees',
    balloon: 'Balloons',
    kite: 'Kites',
    trampoline: 'Trampolines'
  };
  const first = $derived(data.odd.words[0]);
</script>

<Meta
  title="The odd ones"
  description="Swans, cows, trampolines and sunlight on signals: the strangest reasons Britain's trains were late since 2018, counted."
/>

<div class="odd">
  <header>
    <h1>The odd ones</h1>
    <p class="intro">
      Not every delay is a signal failure. Since April 2018, {plurals[first[0]].toLowerCase()} alone turn
      up in {minutes(first[1])} incidents that cost passenger trains {minutes(first[2])} minutes.
    </p>
  </header>

  <section aria-labelledby="words">
    <h2 id="words">Things on the line</h2>
    <p class="note">
      Counted from the few words Network Rail's controllers type for each incident, matching a fixed
      list, after incidents involving people are taken out. Counts only, never the text itself, and
      a "tree" can be a branch.
    </p>
    <ul class="words">
      {#each data.odd.words as [word, incidents, value] (word)}
        <li>
          <span class="name">{plurals[word]}</span>
          <span class="count">{minutes(incidents)}</span>
          <span class="unit">incidents, {minutes(value)} minutes</span>
        </li>
      {/each}
    </ul>
  </section>

  <section aria-labelledby="codes">
    <h2 id="codes">The strangest cause codes</h2>
    <p class="note">
      Some of the odder codes in Network Rail's book, ranked by delay minutes since 2018.
    </p>
    <table>
      <thead>
        <tr>
          <th scope="col">Code</th>
          <th scope="col">What it's for</th>
          <th scope="col" class="num">Incidents</th>
          <th scope="col" class="num">Minutes</th>
        </tr>
      </thead>
      <tbody>
        {#each data.odd.codes as [code, description, incidents, value] (code)}
          <tr>
            <td class="code">{code}</td>
            <td>{description}</td>
            <td class="num">{minutes(incidents)}</td>
            <td class="num">{minutes(value)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </section>
</div>

<style>
  .odd {
    display: grid;
    gap: var(--space-7);
  }

  header {
    display: grid;
    gap: var(--space-4);

    h1 {
      font-size: var(--step-3);
    }
  }

  .intro {
    font-size: var(--step-1);
    max-width: var(--measure);
  }

  section {
    display: grid;
    gap: var(--space-4);

    h2 {
      font-size: var(--step-1);
    }
  }

  .note {
    color: var(--text-muted);
    max-width: var(--measure);
  }

  .words {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 14rem), 1fr));
    border-top: 1px solid var(--rule);
    border-left: 1px solid var(--rule);

    li {
      display: grid;
      gap: var(--space-1);
      padding: var(--space-4);
      border-right: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
    }
  }

  .name {
    color: var(--text-muted);
  }

  .count {
    font-family: var(--font-board);
    font-weight: 700;
    font-size: var(--step-3);
    color: var(--figure);
    line-height: 1;
  }

  .unit {
    font-size: var(--step--1);
    color: var(--text-muted);
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
    vertical-align: top;
  }

  th {
    color: var(--text-faint);
    font-weight: 400;
  }

  .code {
    font-weight: 700;
    color: var(--text-muted);
  }

  .num {
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }
</style>
