<script lang="ts">
  import type { Breakdown, Group, Period } from '#lib/data.ts';
  import { cause } from '#lib/causes.ts';
  import { minutes } from '#lib/format.ts';

  let {
    breakdown,
    groups,
    periods,
    at = $bindable(),
    name
  }: {
    breakdown: Breakdown;
    groups: Group[];
    periods: Period[];
    at: number;
    name: string;
  } = $props();

  const SETTLED = 0.94;
  const WIDTH = 12;
  const HEIGHT = 200;

  const span = $derived(periods.slice(0, breakdown.knock.length));
  const stacks = $derived(
    span.map((period, i) => {
      let base = 0;
      const parts = groups.flatMap((g) => {
        const value = (breakdown.minutes[g.id]?.[i] ?? 0) / period.days;
        const part = { id: g.id, from: base, value };
        base += value;
        return value > 0 ? [part] : [];
      });
      return { period, i, parts, total: base };
    })
  );
  const top = $derived(Math.max(...stacks.map((s) => s.total), 1));
  const ticks = $derived(niceTicks(top));
  const years = $derived(stacks.filter((s) => s.period.id.endsWith('P01')));

  function niceTicks(max: number) {
    const step = 10 ** Math.floor(Math.log10(max));
    const unit = max / step > 5 ? step * 2 : max / step > 2 ? step : step / 2;
    return Array.from({ length: Math.floor(max / unit) }, (_, k) => (k + 1) * unit);
  }

  const y = (value: number) => HEIGHT - (value / top) * HEIGHT;
</script>

<figure class="history">
  <svg
    viewBox="0 0 {span.length * WIDTH} {HEIGHT}"
    preserveAspectRatio="none"
    role="img"
    aria-label="Delay minutes a day picked up {name} in each four-week period from {span[0]
      .label} to {span[span.length - 1].label}, stacked by cause. The CSV has every figure."
  >
    {#each ticks as tick (tick)}
      <line class="grid" x1="0" x2={span.length * WIDTH} y1={y(tick)} y2={y(tick)} />
    {/each}
    {#each stacks as stack (stack.period.id)}
      <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
      <g
        class="bar"
        class:picked={stack.i === at}
        onclick={() => stack.period.file && (at = stack.i)}
      >
        <rect class="hit" x={stack.i * WIDTH} y="0" width={WIDTH} height={HEIGHT} />
        {#if stack.period.file}
          {#each stack.parts as part (part.id)}
            <rect
              x={stack.i * WIDTH + 1}
              y={y(part.from + part.value)}
              width={WIDTH - 2}
              height={(part.value / top) * HEIGHT}
              style:fill={cause(part.id)}
            />
          {/each}
          {#if (stack.period.agreed ?? 1) < SETTLED}
            <rect
              x={stack.i * WIDTH + 1}
              y={y(stack.total)}
              width={WIDTH - 2}
              height={(stack.total / top) * HEIGHT}
              fill="url(#hatch)"
            />
          {/if}
        {:else}
          <rect class="gap" x={stack.i * WIDTH + 1} y="0" width={WIDTH - 2} height={HEIGHT} />
        {/if}
      </g>
    {/each}
  </svg>
  <div class="axis" aria-hidden="true">
    {#each years as year (year.period.id)}
      <span style:left="{(year.i / span.length) * 100}%">{year.period.id.slice(0, 7)}</span>
    {/each}
  </div>
  <figcaption>
    Delay minutes a day, period by period. Gridlines every {minutes(ticks[0] ?? top)} minutes. Hatched
    periods were under 94% agreed when their file came out, so they may still move. Pick a bar to see
    that period.
  </figcaption>
</figure>

<style>
  .history {
    margin: 0;
    display: grid;
    gap: var(--space-2);

    svg {
      width: 100%;
      height: 12rem;
      display: block;
      overflow: visible;
    }
  }

  .grid {
    stroke: var(--rule);
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
  }

  .bar {
    cursor: pointer;

    .hit {
      fill: transparent;
    }

    &:hover .hit,
    &.picked .hit {
      fill: var(--panel-raised);
    }

    &.picked .hit {
      stroke: var(--figure);
      stroke-width: 1;
      vector-effect: non-scaling-stroke;
    }
  }

  .gap {
    fill: none;
    stroke: var(--rule-strong);
    stroke-dasharray: 3 3;
    vector-effect: non-scaling-stroke;
  }

  .axis {
    position: relative;
    height: 1.2rem;
    border-top: 1px solid var(--rule-strong);
    color: var(--text-faint);
    font-size: var(--step--1);
    font-variant-numeric: tabular-nums;

    span {
      position: absolute;
      top: var(--space-1);
      white-space: nowrap;
    }
  }

  @media (max-width: 36rem) {
    .axis span:nth-child(even) {
      display: none;
    }
  }

  figcaption {
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: var(--measure);
  }
</style>
