<script lang="ts">
  import type { Breakdown, Group, Period } from '#lib/data.ts';
  import { cause } from '#lib/causes.ts';
  import { isProvisional } from '#lib/compare.ts';
  import { minutes, months, percent, span } from '#lib/format.ts';
  import ChartTip, { pointerIn } from './ChartTip.svelte';

  let {
    breakdown,
    groups,
    periods,
    at = $bindable(),
    name,
    handover
  }: {
    breakdown: Pick<Breakdown, 'minutes'>;
    groups: Group[];
    periods: Period[];
    at: number;
    name: string;
    /** where Network Rail's own files stop and ORR's figures take over, if they do */
    handover?: number;
  } = $props();

  const has = (p: Period, i: number) => !!p.file || (handover != null && i >= handover);

  const WIDTH = 12;
  const HEIGHT = 200;

  // the chart runs as far as the figures do
  const range = $derived(
    periods.slice(0, Math.max(0, ...Object.values(breakdown.minutes).map((s) => s.length)))
  );
  const stacks = $derived(
    range.map((period, i) => {
      let base = 0;
      const parts = groups.flatMap((g) => {
        const value = (breakdown.minutes[g.id]?.[i] ?? 0) / period.days;
        const part = { id: g.id, label: g.label, from: base, value };
        base += value;
        return value > 0 ? [part] : [];
      });
      return { period, i, parts, total: base };
    })
  );
  const top = $derived(Math.max(...stacks.map((s) => s.total), 1) * 1.12);
  const ticks = $derived(niceTicks(top));
  const years = $derived(stacks.filter((s) => s.period.id.endsWith('P01')));
  const filed = $derived(stacks.filter((s) => has(s.period, s.i) && s.total > 0));
  const notes = $derived.by(() => {
    if (filed.length < 3) return [];
    const high = filed.reduce((a, b) => (b.total > a.total ? b : a));
    const low = filed.reduce((a, b) => (b.total < a.total ? b : a));
    return [
      { s: high, text: `Highest: ${minutes(high.total)} a day, ${months(high.period)}` },
      { s: low, text: `Lowest: ${minutes(low.total)} a day, ${months(low.period)}` }
    ].map(({ s, text }) => {
      const left = ((s.i + 0.5) / range.length) * 100;
      return {
        id: s.period.id,
        text,
        left,
        bottom: (s.total / top) * 100,
        align: left > 78 ? 'end' : left < 22 ? 'start' : 'middle'
      };
    });
  });

  let plot: HTMLDivElement;
  let plotWidth = $state(0);
  let plotHeight = $state(0);
  let hover: number | null = $state(null);
  let focused = $state(false);
  let pointer = $state({ x: 0, y: 0 });

  const shown = $derived(hover ?? (focused ? at : null));
  const tip = $derived(shown == null ? null : stacks[shown]);
  const tipAt = $derived(
    hover != null
      ? pointer
      : {
          x: ((at + 0.5) / range.length) * plotWidth,
          y: (1 - (stacks[at]?.total ?? 0) / top) * plotHeight
        }
  );

  function track(event: PointerEvent) {
    pointer = pointerIn(plot, event);
    const column = Math.floor((pointer.x / plotWidth) * range.length);
    hover = Math.max(0, Math.min(range.length - 1, column));
  }

  function pick() {
    if (hover != null && has(stacks[hover].period, hover)) at = hover;
  }

  function step(event: KeyboardEvent) {
    const choices = filed.map((s) => s.i);
    const here = choices.indexOf(at);
    const to = (
      {
        ArrowLeft: here - 1,
        ArrowDown: here - 1,
        ArrowRight: here + 1,
        ArrowUp: here + 1,
        Home: 0,
        End: choices.length - 1
      } as Record<string, number>
    )[event.key];
    if (to == null) return;
    event.preventDefault();
    hover = null;
    at = choices[Math.max(0, Math.min(choices.length - 1, to))];
  }

  function niceTicks(max: number) {
    const step = 10 ** Math.floor(Math.log10(max));
    const unit = max / step > 5 ? step * 2 : max / step > 2 ? step : step / 2;
    return Array.from({ length: Math.floor(max / unit) }, (_, k) => (k + 1) * unit);
  }

  const y = (value: number) => HEIGHT - (value / top) * HEIGHT;
</script>

<figure class="history">
  <div
    class="plot"
    bind:this={plot}
    bind:clientWidth={plotWidth}
    bind:clientHeight={plotHeight}
    role="slider"
    tabindex="0"
    aria-label="Delay a day {name}, month by month"
    aria-valuemin={filed[0]?.i ?? 0}
    aria-valuemax={filed[filed.length - 1]?.i ?? 0}
    aria-valuenow={at}
    aria-valuetext="{span(periods[at])}, {minutes(stacks[at]?.total)} minutes a day"
    onpointermove={track}
    onpointerleave={() => (hover = null)}
    onclick={pick}
    onkeydown={step}
    onfocus={() => (focused = true)}
    onblur={() => (focused = false)}
  >
    <svg
      viewBox="0 0 {range.length * WIDTH} {HEIGHT}"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      {#each ticks as tick (tick)}
        <line class="grid" x1="0" x2={range.length * WIDTH} y1={y(tick)} y2={y(tick)} />
      {/each}
      {#each stacks as stack (stack.period.id)}
        <g class="bar" class:picked={stack.i === at} class:hovered={stack.i === shown}>
          <rect class="hit" x={stack.i * WIDTH} y="0" width={WIDTH} height={HEIGHT} />
          {#if has(stack.period, stack.i)}
            {#each stack.parts as part (part.id)}
              <rect
                x={stack.i * WIDTH + 1}
                y={y(part.from + part.value)}
                width={WIDTH - 2}
                height={(part.value / top) * HEIGHT}
                style:fill={cause(part.id)}
              />
            {/each}
            {#if isProvisional(stack.period.agreed)}
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
    {#if handover != null && handover < range.length}
      <div class="handover" style:left="{(handover / range.length) * 100}%" aria-hidden="true">
        <span>ORR's figures from here</span>
      </div>
    {/if}
    <div class="ticks" aria-hidden="true">
      {#each ticks as tick (tick)}
        <span style:bottom="{(tick / top) * 100}%">{minutes(tick)}</span>
      {/each}
    </div>
    <div class="notes" class:faded={tip != null} aria-hidden="true">
      {#each notes as note (note.id)}
        <span class="note {note.align}" style:left="{note.left}%" style:bottom="{note.bottom}%">
          {note.text}
        </span>
      {/each}
    </div>
    <ChartTip show={tip != null} x={tipAt.x} y={tipAt.y} bounds={plotWidth} beside>
      {#if tip}
        <span class="tip-when">{span(tip.period)}</span>
        {#if has(tip.period, tip.i)}
          <span class="tip-main">{minutes(tip.total)} minutes a day</span>
          <ul class="tip-rows">
            {#each [...tip.parts].sort((a, b) => b.value - a.value) as part (part.id)}
              <li>
                <span class="chip" style:background={cause(part.id)}></span>
                <span>{part.label}</span>
                <span class="value">{minutes(part.value)}</span>
              </li>
            {/each}
          </ul>
          {#if isProvisional(tip.period.agreed)}
            <span class="tip-note">
              Only {percent(tip.period.agreed ?? 0)} was agreed when published, so it could still change.
            </span>
          {/if}
          {#if handover != null && tip.i >= handover}
            <span class="tip-hint">From ORR's figures, which include autumn in weather.</span>
          {/if}
          <span class="tip-hint">
            {tip.i === at ? 'Showing this month above' : 'Click to show this month above'}
          </span>
        {:else}
          <span class="tip-main">No open figures</span>
          <span class="tip-hint">Network Rail hasn't published this month openly.</span>
        {/if}
      {/if}
    </ChartTip>
  </div>
  <div class="axis" aria-hidden="true">
    {#each years as year (year.period.id)}
      <span style:left="{(year.i / range.length) * 100}%">{year.period.id.slice(0, 7)}</span>
    {/each}
  </div>
  <p class="said">{notes.map((n) => n.text).join('. ')}.</p>
  <figcaption>
    Minutes of delay a day in each month, coloured by cause. Striped bars weren't fully agreed when
    published, so they could still change. Hover over a bar for details, or click it to show that
    month. Arrow keys work too.
  </figcaption>
</figure>

<style>
  .history {
    margin: 0;
    display: grid;
    gap: var(--space-2);
    padding: var(--space-7) var(--space-4) var(--space-4);
    background: var(--panel);
    border-radius: var(--radius);
    min-width: 0;
  }

  .plot {
    position: relative;
    margin-left: 3.5rem;
    cursor: pointer;
    touch-action: pan-y;

    svg {
      width: 100%;
      height: 14rem;
      display: block;
      overflow: visible;
    }

    &:focus-visible {
      outline-offset: 6px;
    }
  }

  .handover {
    position: absolute;
    top: -2.9rem;
    bottom: 0;
    border-left: 2px dashed var(--text-muted);
    pointer-events: none;

    span {
      position: absolute;
      top: 0;
      left: var(--space-2);
      white-space: nowrap;
      font-size: 0.8125rem;
      font-weight: 700;
      color: var(--text-muted);
    }
  }

  .ticks span {
    position: absolute;
    right: calc(100% + var(--space-2));
    translate: 0 50%;
    font-size: var(--step--1);
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }

  .notes {
    transition: opacity 150ms ease-out;

    &.faded {
      opacity: 0.15;
    }
  }

  .notes .note {
    position: absolute;
    translate: -50% 0;
    margin-bottom: var(--space-2);
    padding: 0 var(--space-2);
    background: var(--panel);
    color: var(--text);
    box-shadow: inset 0 0 0 1.5px var(--sign);
    border-radius: var(--radius-chip);
    font-size: 0.8125rem;
    font-weight: 700;
    white-space: nowrap;
    pointer-events: none;

    &.start {
      translate: -0.4rem 0;
    }

    &.end {
      translate: calc(-100% + 0.4rem) 0;
    }
  }

  .grid {
    stroke: var(--rule);
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
  }

  .bar {
    .hit {
      fill: transparent;
    }

    &.hovered .hit {
      fill: var(--panel-raised);
    }

    &.picked .hit {
      fill: rgb(255 204 0 / 0.35);
      stroke: var(--sign);
      stroke-width: 2;
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
    height: 1.4rem;
    margin-left: 3.5rem;
    border-top: 3px solid var(--sign);
    color: var(--text-muted);
    font-size: var(--step--1);
    font-weight: 600;
    font-variant-numeric: tabular-nums;

    span {
      position: absolute;
      top: var(--space-1);
      white-space: nowrap;
    }
  }

  .said {
    display: none;
    font-size: var(--step--1);
    font-weight: 600;
  }

  @media (max-width: 36rem) {
    .axis span:nth-child(even) {
      display: none;
    }

    .notes {
      display: none;
    }

    .said {
      display: block;
    }
  }

  figcaption {
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: var(--measure);
    padding-top: var(--space-2);
  }
</style>
