<script lang="ts">
  import { things } from '#lib/causes.ts';
  import { minutes } from '#lib/format.ts';
  import ChartTip, { pointerIn } from '#lib/components/ChartTip.svelte';
  import Figure from '#lib/components/Figure.svelte';
  import Meta from '#lib/components/Meta.svelte';
  import Pictogram, { hasPictogram } from '#lib/components/Pictogram.svelte';

  let { data } = $props();

  const words = $derived(data.odd.words);
  const first = $derived(words[0]);
  const longest = $derived(Math.max(...words.map(([, , value]) => value)));
  const longestCode = $derived(Math.max(...data.odd.codes.map(([, , , value]) => value)));

  type Tip = { name: string; incidents: number; value: number };
  let page: HTMLDivElement;
  let pageWidth = $state(0);
  let tip: Tip | null = $state(null);
  let pointer = $state({ x: 0, y: 0 });

  function show(event: PointerEvent, row: Tip) {
    pointer = pointerIn(page, event);
    tip = row;
  }
</script>

<Meta
  title="The odd ones"
  description="Swans, cows, trampolines and sunlight on signals: the strangest reasons Britain's trains were late since 2018, counted."
/>

<div class="odd" bind:this={page} bind:clientWidth={pageWidth}>
  <header>
    <h1>The odd ones</h1>
    <p class="intro">
      Not every delay is a signal failure. Since April 2018, {things[first[0]].toLowerCase()} alone turn
      up in this many incidents on the line:
    </p>
  </header>

  <section class="lead" aria-label={things[first[0]]}>
    <Figure value={first[1]} unit="incidents" />
    <p>They cost passenger trains {minutes(first[2])} minutes.</p>
  </section>

  <section aria-labelledby="words">
    <h2 id="words">Things on the line</h2>
    <p class="note">
      Counted from the short notes Network Rail's controllers write about each incident. We only
      count the words, and never show the notes. A "tree" can also be a branch.
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
            <th scope="row">
              <span class="thing">
                <span class="pict" class:blank={!hasPictogram(word)}>
                  {#if hasPictogram(word)}<Pictogram name={word} />{/if}
                </span>
                <span class="word">{things[word]}</span>
              </span>
            </th>
            <td class="num">{minutes(incidents)}</td>
            <td class="num">{minutes(value)}</td>
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <td
              class="bar"
              onpointermove={(e) => show(e, { name: things[word], incidents, value })}
              onpointerleave={() => (tip = null)}
            >
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
      Some of Network Rail's odder cause codes, ranked by minutes of delay since 2018.
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
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <td
              class="bar"
              onpointermove={(e) => show(e, { name: `${code}, ${description}`, incidents, value })}
              onpointerleave={() => (tip = null)}
            >
              <span style:width="{Math.max((value / longestCode) * 100, 0.5)}%"></span>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </section>
  <ChartTip show={tip != null} x={pointer.x} y={pointer.y} bounds={pageWidth}>
    {#if tip}
      <span class="tip-when">{tip.name}</span>
      <span class="tip-main">{minutes(tip.value)} minutes of delay</span>
      <span>
        From {minutes(tip.incidents)} incidents since April 2018, so about {minutes(
          tip.value / tip.incidents
        )} minutes each.
      </span>
    {/if}
  </ChartTip>
</div>

<style>
  .odd {
    position: relative;
    display: grid;
    gap: var(--space-7);
  }

  .thing {
    display: inline-flex;
    align-items: center;
    gap: var(--space-3);
  }

  .word {
    padding-top: 0.2em;
  }

  .pict {
    flex: none;
    width: 2rem;
    height: 2rem;
    padding: 0.3rem;
    border-radius: var(--radius-chip);
    background: var(--sign);
    color: var(--on-sign);

    &.blank {
      background: none;
    }
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
    cursor: crosshair;

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
