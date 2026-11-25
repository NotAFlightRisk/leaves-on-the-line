<script lang="ts">
  import Meta from '#lib/components/Meta.svelte';
  import { minutes } from '#lib/format.ts';

  let { data } = $props();

  const letters = $derived(
    Object.entries(Object.groupBy(data.stations, ([, name]) => name[0].toUpperCase())).sort(
      ([a], [b]) => a.localeCompare(b)
    )
  );
</script>

<Meta
  title="Every station"
  description="All {data.stations.length.toLocaleString(
    'en-GB'
  )} stations in Britain with delay records since 2018, A to Z."
/>

<h1>Every station, A to Z</h1>
<p class="intro">
  {minutes(data.stations.length)} stations with delay picked up at them since April 2018. Each has its
  own page.
</p>

<nav class="letters" aria-label="Jump to a letter">
  {#each letters as [letter] (letter)}
    <a href="#letter-{letter}">{letter}</a>
  {/each}
</nav>

{#each letters as [letter, stations = []] (letter)}
  <section aria-labelledby="letter-{letter}">
    <h2 id="letter-{letter}">{letter}</h2>
    <ul>
      {#each stations as [crs, name] (crs)}
        <li><a href="/station/{crs}">{name}</a></li>
      {/each}
    </ul>
  </section>
{/each}

<style>
  h1 {
    font-size: var(--step-3);
  }

  .intro {
    margin-top: var(--space-3);
    color: var(--text-muted);
  }

  .letters {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1) var(--space-3);
    margin: var(--space-5) 0;
    font-weight: 700;
  }

  section {
    margin-top: var(--space-6);
    scroll-margin-top: var(--space-4);
  }

  h2 {
    color: var(--figure);
    font-size: var(--step-2);
    border-bottom: 1px solid var(--rule);
    padding-bottom: var(--space-2);
  }

  ul {
    list-style: none;
    margin: var(--space-3) 0 0;
    padding: 0;
    columns: 14rem;
    column-gap: var(--space-6);

    li {
      padding-block: 0.15rem;
      break-inside: avoid;
    }
  }
</style>
