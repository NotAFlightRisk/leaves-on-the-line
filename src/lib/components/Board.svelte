<script lang="ts">
  import type { Breakdown, Group, Period } from '#lib/data.ts';
  import { cause, covers } from '#lib/causes.ts';
  import { describeStanding, share, standing, totalAt } from '#lib/compare.ts';
  import { minutes, percent } from '#lib/format.ts';

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
        standing: compare ? standing(series, periods, at) : null
      };
    })
  );

  const scale = (row: (typeof rows)[number]) =>
    Math.max(row.standing?.high ?? 0, row.standing?.perDay ?? 0) * 1.08 || 1;
</script>

<table class="board">
  <caption class="visually-hidden">Delay minutes by cause in {periods[at].label}</caption>
  <thead>
    <tr>
      <th scope="col">Cause</th>
      <th scope="col" class="num">Minutes</th>
      <th scope="col" class="num">Share</th>
      <th scope="col" class="num wide">Network-wide</th>
      {#if compare}<th scope="col" class="range">
          A day, against the same period other years
        </th>{/if}
      <th scope="col" class="num wide">Trains cancelled</th>
    </tr>
  </thead>
  {#each sides as [side, title] (side)}
    <tbody>
      <tr class="side">
        <th scope="rowgroup" colspan={compare ? 6 : 5}>{title} causes</th>
      </tr>
      {#each rows.filter((r) => r.group.side === side) as row (row.group.id)}
        <tr class:empty={!row.value}>
          <th scope="row">
            <span class="chip" style:background={cause(row.group.id)}></span>
            <span class="name" title={covers[row.group.id]}>{row.group.label}</span>
          </th>
          <td class="num minutes">{row.value ? minutes(row.value) : '-'}</td>
          <td class="num">{row.value ? percent(row.portion) : '-'}</td>
          <td class="num wide muted">{percent(row.networkPortion)}</td>
          {#if compare}
            <td class="range">
              {#if row.standing}
                {@const s = row.standing}
                {@const max = scale(row)}
                <svg viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true">
                  <rect class="track" x="0" y="5" width="100" height="2" />
                  <rect
                    class="usual"
                    x={(s.low / max) * 100}
                    y="3"
                    width={Math.max(((s.high - s.low) / max) * 100, 0.8)}
                    height="6"
                  />
                  <rect
                    class="mark"
                    x={(s.perDay / max) * 100 - 0.9}
                    y="0"
                    width="1.8"
                    height="12"
                    style:fill={cause(row.group.id)}
                  />
                </svg>
                <span class="words">{minutes(s.perDay)} a day, {describeStanding(s)}</span>
              {:else}
                <span class="words muted">Not enough other years</span>
              {/if}
            </td>
          {/if}
          <td class="num wide">{row.cancelled ? minutes(row.cancelled) : '-'}</td>
        </tr>
      {/each}
    </tbody>
  {/each}
</table>

<style>
  .board {
    width: 100%;
    font-size: var(--step--1);

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
    padding-top: var(--space-5);
    color: var(--text-muted);
    font-weight: 700;
    letter-spacing: 0.02em;
    border-bottom-color: var(--rule-strong);
  }

  tbody th[scope='row'] {
    font-weight: 400;
    white-space: nowrap;
  }

  .chip {
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
    margin-right: var(--space-2);
    border-radius: 2px;
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

  .empty {
    color: var(--text-faint);

    .chip {
      opacity: 0.45;
    }
  }

  .range {
    min-width: 14rem;

    svg {
      display: block;
      width: 100%;
      height: 0.75rem;
    }

    .track {
      fill: var(--rule);
    }

    .usual {
      fill: var(--rule-strong);
    }
  }

  .words {
    display: block;
    margin-top: var(--space-1);
    color: var(--text-muted);
  }

  @media (max-width: 48rem) {
    .wide {
      display: none;
    }

    .range {
      min-width: 9rem;
    }
  }
</style>
