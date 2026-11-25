<script lang="ts">
  import { cause } from '#lib/causes.ts';
  import { minutes } from '#lib/format.ts';
  import Meta from '#lib/components/Meta.svelte';
  import PlacePage from '#lib/components/PlacePage.svelte';

  let { data } = $props();

  const place = $derived(data.place);
  const worst = $derived(
    data.index.groups
      .filter((g) => place.sections?.[g.id]?.length)
      .map((g) => ({
        group: g,
        rows: place.sections?.[g.id] ?? []
      }))
  );
</script>

<Meta
  title="Why trains were late on the {place.name} route"
  description="What made passenger trains late on Network Rail's {place.name} route, cause by cause since 2018, with the ten worst stretches of line for each cause."
/>

<PlacePage
  {place}
  index={data.index}
  where="on the {place.name} route"
  heading="{place.name} route"
  counts="Delay picked up anywhere Network Rail files under its {place.name} route, stations, junctions and sidings alike, using today's route map for every year."
>
  <section aria-labelledby="worst">
    <h2 id="worst">Worst stretches since 2018</h2>
    <p class="intro">
      Where the incidents started, by cause, counting all the knock-on delay they caused anywhere.
    </p>
    <div class="worst">
      {#each worst as { group, rows } (group.id)}
        <table>
          <caption>
            <span class="chip" style:background={cause(group.id)}></span>{group.label}
          </caption>
          <tbody>
            {#each rows as [name, value] (name)}
              <tr>
                <td>{name}</td>
                <td class="num">{minutes(value)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/each}
    </div>
  </section>
</PlacePage>

<style>
  section {
    display: grid;
    gap: var(--space-4);

    h2 {
      font-size: var(--step-1);
    }
  }

  .intro {
    color: var(--text-muted);
    max-width: var(--measure);
  }

  .worst {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 20rem), 1fr));
    gap: var(--space-5) var(--space-6);
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

  .chip {
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
    margin-right: var(--space-2);
    border-radius: 2px;
  }

  td {
    padding: var(--space-1) var(--space-2);
    border-bottom: 1px solid var(--rule);
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
</style>
