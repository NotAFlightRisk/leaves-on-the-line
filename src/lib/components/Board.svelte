<script lang="ts">
  import type { Breakdown, Group, Period } from '#lib/data.ts';
  import { cause, covers } from '#lib/causes.ts';
  import { describeStanding, share, siblings, standing, totalAt } from '#lib/compare.ts';
  import { minutes, percent, span } from '#lib/format.ts';
  import ChartTip, { pointerIn } from './ChartTip.svelte';
  import Rolling from './Rolling.svelte';

  let {
    breakdown,
    network,
    groups,
    periods,
    at,
    compare
  }: {
    breakdown: Breakdown;
    network: Breakdown;
    groups: Group[];
    periods: Period[];
    at: number;
    compare: boolean;
  } = $props();

  const total = $derived(totalAt(breakdown, at));
  const networkTotal = $derived(totalAt(network, at));
  const sides = [
    ['nr', "Network Rail's"],
    ['op', "The operators'"]
  ] as const;

  const rows = $derived(
    groups.map((group) => {
      const series = breakdown.minutes[group.id] ?? [];
      const value = series[at] ?? 0;
      return {
        group,
        value,
        portion: share(value, total),
        networkPortion: share(network.minutes[group.id]?.[at] ?? 0, networkTotal),
        cancelled: breakdown.cancelled[group.id]?.[at] ?? 0,
        standing: compare ? standing(series, periods, at) : null,
        years: [...siblings(periods, at), at]
          .filter((i) => i < series.length)
          .sort((a, b) => a - b)
          .map((i) => ({
            id: periods[i].id,
            year: periods[i].id.slice(0, 7),
            value: (series[i] ?? 0) / periods[i].days,
            mine: i === at
          }))
      };
    })
  );

  type Row = (typeof rows)[number];
  let wrap: HTMLDivElement;
  let wrapWidth = $state(0);
  let tip: { kind: 'share' | 'range'; row: Row } | null = $state(null);
  let pointer = $state({ x: 0, y: 0 });

  function show(event: PointerEvent, kind: 'share' | 'range', row: Row) {
    pointer = pointerIn(wrap, event);
    tip = { kind, row };
  }

  // the range bar runs a little past the highest year, so its mark never sits on the edge
  const scale = (row: Row) =>
    Math.max(row.standing?.high ?? 0, row.standing?.perDay ?? 0) * 1.08 || 1;
</script>

<p class="key">
  The tick on each share bar is that cause's share across the whole network.
  {#if compare}The grey range covers the same month in other years, per day, and the coloured mark
    is this year.{/if} Hover over a bar for the exact figures.
</p>
<div class="wrap" bind:this={wrap} bind:clientWidth={wrapWidth}>
  <table class="board">
    <caption class="visually-hidden">Delay minutes by cause, {span(periods[at])}</caption>
    <thead>
      <tr>
        <th scope="col">Cause</th>
        <th scope="col" class="num">Minutes</th>
        <th scope="col">Share</th>
        {#if compare}<th scope="col" class="range">A day, against other years</th>{/if}
        <th scope="col" class="num cancelled">Trains cancelled</th>
      </tr>
    </thead>
    {#each sides as [side, title] (side)}
      <tbody>
        <tr class="side">
          <th scope="rowgroup" colspan={compare ? 5 : 4}>{title} causes</th>
        </tr>
        {#each rows.filter((r) => r.group.side === side) as row (row.group.id)}
          <tr class:empty={!row.value}>
            <th scope="row" class="cause">
              <span class="chip" style:background={cause(row.group.id)}></span>
              <span title={covers[row.group.id]}>{row.group.label}</span>
            </th>
            <td class="num minutes"><Rolling value={row.value} format={minutes} /></td>
            <td class="share">
              <span>{percent(row.portion)}</span>
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <svg
                viewBox="0 0 100 10"
                preserveAspectRatio="none"
                aria-hidden="true"
                onpointermove={(e) => show(e, 'share', row)}
                onpointerleave={() => (tip = null)}
              >
                <rect class="track" x="0" y="3" width="100" height="4" />
                <rect
                  x="0"
                  y="3"
                  width={row.portion * 100}
                  height="4"
                  style:fill={cause(row.group.id)}
                />
                <rect
                  class="tick"
                  x={row.networkPortion * 100 - 0.75}
                  y="0"
                  width="1.5"
                  height="10"
                />
              </svg>
              <span class="muted">network {percent(row.networkPortion)}</span>
            </td>
            {#if compare}
              <td class="range">
                {#if row.standing}
                  {@const s = row.standing}
                  {@const max = scale(row)}
                  <!-- svelte-ignore a11y_no_static_element_interactions -->
                  <svg
                    viewBox="0 0 100 12"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                    onpointermove={(e) => show(e, 'range', row)}
                    onpointerleave={() => (tip = null)}
                  >
                    <rect class="track" x="0" y="5" width="100" height="2" />
                    <rect
                      class="usual"
                      x={(s.low / max) * 100}
                      y="3"
                      width={Math.max(((s.high - s.low) / max) * 100, 0.8)}
                      height="6"
                    />
                    <rect
                      x={(s.perDay / max) * 100 - 0.9}
                      y="0"
                      width="1.8"
                      height="12"
                      style:fill={cause(row.group.id)}
                    />
                  </svg>
                  <span class="words muted">{minutes(s.perDay)} a day, {describeStanding(s)}</span>
                {:else}
                  <span class="words muted">Not enough other years</span>
                {/if}
              </td>
            {/if}
            <td class="num cancelled" class:none={!row.cancelled}>
              {row.cancelled ? minutes(row.cancelled) : '-'}<span class="unit muted">
                {` ${row.cancelled === 1 ? 'train' : 'trains'} cancelled`}
              </span>
            </td>
          </tr>
        {/each}
      </tbody>
    {/each}
  </table>
  <ChartTip show={tip != null} x={pointer.x} y={pointer.y} bounds={wrapWidth}>
    {#if tip}
      {@const r = tip.row}
      <span class="tip-when">{r.group.label}</span>
      {#if tip.kind === 'share'}
        <span class="tip-main">{percent(r.portion)} of the delay here</span>
        <span>
          {minutes(r.value)} minutes. Across the whole network this cause was {percent(
            r.networkPortion
          )}.
        </span>
      {:else if r.standing}
        <span class="tip-main">{minutes(r.standing.perDay)} minutes a day</span>
        <span>The same month in each year:</span>
        <ul class="tip-rows">
          {#each r.years as y (y.id)}
            <li>
              <span
                class="chip"
                style:background={y.mine ? cause(r.group.id) : 'var(--on-sign-muted)'}
              ></span>
              <span class:mine={y.mine}>{y.year}{y.mine ? ', this one' : ''}</span>
              <span class="value" class:mine={y.mine}>{minutes(y.value)}</span>
            </li>
          {/each}
        </ul>
        <span class="tip-hint">2020-21 is left out, as lockdown skews it.</span>
      {/if}
    {/if}
  </ChartTip>
</div>

<style>
  .wrap {
    position: relative;
  }

  .share svg,
  .range svg {
    cursor: crosshair;
  }

  .key {
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: var(--measure);
  }

  .board {
    width: 100%;
    font-size: var(--step--1);
    background: var(--panel);
    border-radius: var(--radius);

    th,
    td {
      padding: var(--space-2) var(--space-3);
      border-bottom: 1px solid var(--rule);
      text-align: left;
      vertical-align: middle;
    }

    thead th {
      color: var(--text-faint);
      font-weight: 400;
      border-bottom-color: var(--rule-strong);
    }
  }

  .side th {
    padding-block: var(--space-2);
    background: var(--sign);
    color: var(--on-sign);
    font-size: var(--step-0);
    font-weight: 800;
    border-bottom: 4px solid var(--edge);
  }

  .cause {
    font-weight: 400;
  }

  .chip {
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
    margin-right: var(--space-2);
    border-radius: var(--radius-chip);
    vertical-align: -0.05em;
  }

  .num {
    text-align: right;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
  }

  .minutes {
    font-size: var(--step-0);
    font-weight: 700;
  }

  .muted {
    color: var(--text-muted);
  }

  .share {
    min-width: 8rem;
    font-variant-numeric: tabular-nums;

    svg {
      display: block;
      width: 100%;
      height: 0.6rem;
      margin-block: var(--space-1);
    }

    .tick {
      fill: var(--text);
    }
  }

  .track {
    fill: var(--rule);
  }

  .usual {
    fill: var(--rule-strong);
  }

  .range {
    min-width: 13rem;

    svg {
      display: block;
      width: 100%;
      height: 0.75rem;
    }
  }

  .words {
    display: block;
    margin-top: var(--space-1);
  }

  .unit {
    display: none;
  }

  .empty {
    color: var(--text-faint);

    .chip {
      opacity: 0.45;
    }
  }

  @media (max-width: 48rem) {
    thead {
      display: none;
    }

    tbody tr:not(.side) {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto 6.5rem;
      column-gap: var(--space-3);
      padding-block: var(--space-2);
      border-bottom: 1px solid var(--rule);

      > * {
        padding: 0;
        border: 0;
      }
    }

    .range,
    .cancelled {
      grid-column: 1 / -1;
      min-width: 0;
      text-align: left;
    }

    .range {
      margin-top: var(--space-2);
    }

    .cancelled.none {
      display: none;
    }

    .unit {
      display: inline;
    }

    .share {
      min-width: 0;
    }
  }
</style>
