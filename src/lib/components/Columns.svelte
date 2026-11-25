<script lang="ts">
  import type { Period, Series } from '#lib/data.ts';
  import { minutes } from '#lib/format.ts';

  let {
    ours,
    theirs,
    periods,
    colour,
    label,
    top
  }: {
    ours: Series;
    theirs?: Series;
    periods: Period[];
    colour: string;
    label: string;
    top: number;
  } = $props();

  const WIDTH = 6;
  const HEIGHT = 80;
  const SETTLED = 0.94;

  const perDay = (series: Series | undefined, i: number) =>
    series?.[i] == null ? null : (series[i] as number) / periods[i].days;
  const bars = $derived(
    periods.map((p, i) => ({
      i,
      ours: perDay(ours, i),
      theirs: perDay(theirs, i),
      hatched: (p.agreed ?? 1) < SETTLED
    }))
  );
  const peak = $derived(
    bars.reduce((best, b) => ((b.ours ?? 0) > (best.ours ?? 0) ? b : best), bars[0])
  );
  const h = (value: number) => (Math.min(value, top) / top) * HEIGHT;
</script>

<figure>
  <figcaption>
    <span class="chip" style:background={colour}></span>
    <span class="label">{label}</span>
    <span class="peak">peak {minutes(peak.ours)} a day, {periods[peak.i].label}</span>
  </figcaption>
  <svg
    viewBox="0 0 {periods.length * WIDTH} {HEIGHT}"
    preserveAspectRatio="none"
    role="img"
    aria-label="{label}: delay minutes a day each period. Highest was {minutes(
      peak.ours
    )} a day in {periods[peak.i].label}."
  >
    {#each bars as bar (bar.i)}
      {#if bar.ours != null}
        <rect
          x={bar.i * WIDTH + 0.5}
          y={HEIGHT - h(bar.ours)}
          width={WIDTH - 1}
          height={h(bar.ours)}
          style:fill={colour}
        />
        {#if bar.hatched}
          <rect
            x={bar.i * WIDTH + 0.5}
            y={HEIGHT - h(bar.ours)}
            width={WIDTH - 1}
            height={h(bar.ours)}
            fill="url(#hatch)"
          />
        {/if}
      {:else if bar.theirs != null}
        <rect
          class="theirs"
          x={bar.i * WIDTH + 1}
          y={HEIGHT - h(bar.theirs)}
          width={WIDTH - 2}
          height={h(bar.theirs)}
          style:stroke={colour}
        />
      {/if}
    {/each}
  </svg>
  <div class="ends" aria-hidden="true">
    <span>{periods[0].id.slice(0, 7)}</span>
    <span>{periods[periods.length - 1].id.slice(0, 7)}</span>
  </div>
</figure>

<style>
  figure {
    margin: 0;
    display: grid;
    gap: var(--space-2);
    min-width: 0;
  }

  figcaption {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--space-1) var(--space-2);
    font-size: var(--step--1);
  }

  .chip {
    width: 0.7rem;
    height: 0.7rem;
    border-radius: 2px;
    align-self: center;
  }

  .label {
    font-weight: 700;
  }

  .peak {
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }

  svg {
    width: 100%;
    height: 5rem;
    display: block;
    border-bottom: 1px solid var(--rule-strong);
  }

  .ends {
    display: flex;
    justify-content: space-between;
    margin-top: calc(-1 * var(--space-1));
    color: var(--text-faint);
    font-size: var(--step--1);
    font-variant-numeric: tabular-nums;
  }

  .theirs {
    fill: none;
    stroke-width: 1;
    stroke-dasharray: 2 2;
    vector-effect: non-scaling-stroke;
  }
</style>
