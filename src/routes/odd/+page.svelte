<script lang="ts">
  import { minutes } from '#lib/format.ts';
  import Figure from '#lib/components/Figure.svelte';
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
  const words = $derived(data.odd.words);
  const first = $derived(words[0]);
  const longest = $derived(Math.max(...words.map(([, , value]) => value)));
  const longestCode = $derived(Math.max(...data.odd.codes.map(([, , , value]) => value)));
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
      up in this many incidents on the line:
    </p>
  </header>

  <section class="lead" aria-label={plurals[first[0]]}>
    <Figure value={first[1]} unit="incidents" />
    <p>They cost passenger trains {minutes(first[2])} minutes.</p>
  </section>

  <section aria-labelledby="words">
    <h2 id="words">Things on the line</h2>
    <p class="note">
      Counted from the few words Network Rail's controllers type for each incident, matching a fixed
      list, after incidents involving people are taken out. Counts only, never the text itself, and
      a "tree" can be a branch.
    </p>
    <table>
      <thead>
        <tr>
          <th scope="col">Thing</th>
          <th scope="col" class="num">Incidents</th>
          <th scope="col" class="num">Minutes</th>
          <th scope="col" class="bar"><span class="visually-hidden">Minutes, drawn</span></th>
        </tr>
      </thead>
      <tbody>
        {#each words as [word, incidents, value] (word)}
          <tr>
            <th scope="row">{plurals[word]}</th>
            <td class="num">{minutes(incidents)}</td>
            <td class="num">{minutes(value)}</td>
            <td class="bar">
              <span style:width="{Math.max((value / longest) * 100, 0.5)}%"></span>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
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
          <th scope="col" class="bar"><span class="visually-hidden">Minutes, drawn</span></th>
        </tr>
      </thead>
      <tbody>
        {#each data.odd.codes as [code, description, incidents, value] (code)}
          <tr>
            <td class="code">{code}</td>
            <td>{description}</td>
            <td class="num">{minutes(incidents)}</td>
            <td class="num">{minutes(value)}</td>
            <td class="bar">
              <span style:width="{Math.max((value / longestCode) * 100, 0.5)}%"></span>
            </td>
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

  .lead {
    display: grid;
    gap: var(--space-3);
    margin-top: calc(-1 * var(--space-4));
    padding: var(--space-5) var(--space-5) var(--space-6);
    background: var(--panel);
    border: 1px solid var(--rule);
    border-radius: var(--radius);

    p {
      color: var(--text-muted);
    }
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

  table {
    width: 100%;
    font-size: var(--step--1);
  }

  th,
  td {
    padding: var(--space-2);
    border-bottom: 1px solid var(--rule);
    text-align: left;
    vertical-align: middle;
  }

  thead th {
    color: var(--text-faint);
    font-weight: 400;
  }

  tbody th {
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

  .bar {
    width: 30%;

    span {
      display: block;
      height: 0.5rem;
      background: var(--text-muted);
      border-radius: var(--radius-bar);
    }
  }

  @media (max-width: 40rem) {
    .bar {
      display: none;
    }
  }
</style>
