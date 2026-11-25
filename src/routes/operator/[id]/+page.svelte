<script lang="ts">
  import { share, sum } from '#lib/compare.ts';
  import { minutes, percent } from '#lib/format.ts';
  import ChartTip, { pointerIn } from '#lib/components/ChartTip.svelte';
  import Meta from '#lib/components/Meta.svelte';
  import PlacePage from '#lib/components/PlacePage.svelte';

  let { data } = $props();

  const place = $derived(data.place);
  const who = [
    ['self', 'Their own'],
    ['nr', "Network Rail's"],
    ['other', "Other operators' trains"]
  ] as const;
  const totals = $derived(
    who.map(([key, label]) => ({ key, label, value: sum(place.responsible?.[key] ?? []) }))
  );
  const all = $derived(sum(totals.map((t) => t.value)));
  type Part = (typeof totals)[number];
  const explain: Record<Part['key'], string> = {
    self: 'Delay this operator caused to its own trains.',
    nr: "Delay from Network Rail's causes, like signals, track and how the network was run.",
    other: 'Delay caused by other operators.'
  };

  let split: HTMLDivElement;
  let splitWidth = $state(0);
  let tip: Part | null = $state(null);
  let pointer = $state({ x: 0, y: 0 });

  function show(event: PointerEvent, part: Part) {
    pointer = pointerIn(split, event);
    tip = part;
  }
</script>

<Meta
  title="Why {place.name} trains were late"
  description="What made {place.name} trains late since 2018, cause by cause, and how much of it was their own doing, Network Rail's or other operators'."
/>

<PlacePage
  {place}
  index={data.index}
  where="by {place.name} trains"
  counts="Delay to {place.name}'s passenger trains, wherever it happened and whoever caused it.{place
    .former?.length
    ? ` Earlier years cover ${place.former.join(' and ')}, which ran the same services before.`
    : ''}"
>
  <section aria-labelledby="whose">
    <h2 id="whose">Whose fault, since 2018</h2>
    <div class="holder" bind:this={split} bind:clientWidth={splitWidth}>
      <div
        class="split"
        role="img"
        aria-label={totals.map((t) => `${t.label}: ${percent(share(t.value, all))}`).join(', ')}
      >
        {#each totals as t (t.key)}
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <span
            class="part {t.key}"
            style:flex-grow={t.value}
            onpointermove={(e) => show(e, t)}
            onpointerleave={() => (tip = null)}
          ></span>
        {/each}
      </div>
      <ChartTip show={tip != null} x={pointer.x} y={pointer.y} bounds={splitWidth}>
        {#if tip}
          <span class="tip-when">{tip.label}, since 2018</span>
          <span class="tip-main">{percent(share(tip.value, all))} of the delay</span>
          <span>{minutes(tip.value)} minutes. {explain[tip.key]}</span>
        {/if}
      </ChartTip>
    </div>
    <dl class="key">
      {#each totals as t (t.key)}
        <div>
          <dt><span class="swatch {t.key}"></span>{t.label}</dt>
          <dd>{percent(share(t.value, all))} <span>({minutes(t.value)} minutes)</span></dd>
        </div>
      {/each}
    </dl>
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

  .holder {
    position: relative;
  }

  .split {
    display: flex;
    height: 1.75rem;
    gap: 2px;
    cursor: crosshair;
  }

  .part {
    flex-basis: 0;
  }

  .self {
    background: var(--figure);
  }

  .nr {
    background: var(--text-muted);
  }

  .other {
    background: var(--rule-strong);
  }

  .key {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3) var(--space-6);
    margin: 0;

    dt {
      color: var(--text-muted);
    }

    dd {
      margin: 0;
      font-size: var(--step-1);
      font-weight: 700;

      span {
        font-size: var(--step--1);
        font-weight: 400;
        color: var(--text-muted);
      }
    }
  }

  .swatch {
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
    margin-right: var(--space-2);
    border-radius: var(--radius-chip);
  }
</style>
