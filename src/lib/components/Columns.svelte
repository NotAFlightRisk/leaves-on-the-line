<script lang="ts">
  import type { Period, Series } from '#lib/data.ts';
  import { isProvisional, PERIODS_A_YEAR } from '#lib/compare.ts';
  import { minutes, months, percent, span } from '#lib/format.ts';
  import ChartTip, { pointerIn } from './ChartTip.svelte';

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

  function perDay(series: Series | undefined, i: number) {
    const value = series?.[i];
    return value == null ? null : value / periods[i].days;
  }
  const bars = $derived(
    periods.map((p, i) => ({
      i,
      ours: perDay(ours, i),
      theirs: perDay(theirs, i),
      hatched: isProvisional(p.agreed)
    }))
  );
  const peak = $derived(
    bars.reduce((best, b) => ((b.ours ?? 0) > (best.ours ?? 0) ? b : best), bars[0])
  );
  const peakText = $derived(`${minutes(peak.ours)} a day, ${months(periods[peak.i])}`);
  const h = (value: number) => (Math.min(value, top) / top) * HEIGHT;

  let plot: HTMLDivElement;
  let plotWidth = $state(0);
  let hover: number | null = $state(null);
  let pointer = $state({ x: 0, y: 0 });
  const tip = $derived(hover == null ? null : bars[hover]);
  const yearBefore = $derived(hover == null ? null : (bars[hover - PERIODS_A_YEAR]?.ours ?? null));

  function track(event: PointerEvent) {
    pointer = pointerIn(plot, event);
    const column = Math.floor((pointer.x / plotWidth) * bars.length);
    hover = Math.max(0, Math.min(bars.length - 1, column));
  }
</script>

<figure>
  <figcaption>
    <span class="chip" style:background={colour}></span>
    <span class="label">{label}</span>
    <span class="peak">highest {peakText}</span>
  </figcaption>
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="plot"
    bind:this={plot}
    bind:clientWidth={plotWidth}
    onpointermove={track}
    onpointerleave={() => (hover = null)}
  >
    <svg
      viewBox="0 0 {periods.length * WIDTH} {HEIGHT}"
      preserveAspectRatio="none"
      role="img"
      aria-label="{label}: minutes of delay a day in each month. The highest was {peakText}."
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
        {#if bar.i === hover}
          <rect class="hovered" x={bar.i * WIDTH} y="0" width={WIDTH} height={HEIGHT} />
        {/if}
      {/each}
    </svg>
    <ChartTip show={tip != null} x={pointer.x} y={pointer.y} bounds={plotWidth}>
      {#if tip}
        <span class="tip-when">{span(periods[tip.i])}</span>
        {#if tip.ours != null}
          <span class="tip-main">{minutes(tip.ours)} minutes a day</span>
          <span>{label}, {minutes(ours[tip.i])} minutes over the month.</span>
          {#if yearBefore != null}
            <span class="tip-hint">A year earlier: {minutes(yearBefore)} a day</span>
          {/if}
          {#if tip.hatched}
            <span class="tip-note">
              Only {percent(periods[tip.i].agreed ?? 0)} was agreed when published, so it could still
              change.
            </span>
          {/if}
        {:else if tip.theirs != null}
          <span class="tip-main">{minutes(tip.theirs)} minutes a day</span>
          <span>From ORR's figures. Network Rail's own files stop before this month.</span>
        {:else}
          <span class="tip-main">No figures</span>
        {/if}
      {/if}
    </ChartTip>
  </div>
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
    border-radius: var(--radius-chip);
    align-self: center;
  }

  .label {
    font-weight: 700;
  }

  .peak {
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }

  .plot {
    position: relative;
  }

  .hovered {
    fill: var(--sign);
    opacity: 0.08;
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
