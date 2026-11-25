<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { Breakdown, Group, Period } from '#lib/data.ts';
  import {
    isProvisional,
    isRecord,
    perDay,
    share,
    sum,
    summarise,
    totalAt,
    verdict
  } from '#lib/compare.ts';
  import { dateLong, dateMonth, minutes, percent, spanLong } from '#lib/format.ts';
  import Rolling from './Rolling.svelte';

  let {
    breakdown,
    groups,
    periods,
    at,
    where,
    main = false,
    children
  }: {
    breakdown: Breakdown;
    groups: Group[];
    periods: Period[];
    at: number;
    where: string;
    main?: boolean;
    children?: Snippet;
  } = $props();

  const period = $derived(periods[at]);
  const since = $derived(dateMonth(periods[0].start));
  const total = $derived(totalAt(breakdown, at));
  const day = $derived(perDay(breakdown, periods, at));
  const cancelled = $derived(sum(Object.values(breakdown.cancelled).map((s) => s[at] ?? null)));
  const knock = $derived(share(breakdown.knock[at] ?? 0, total));
  const agreed = $derived(total ? 1 - (breakdown.unagreed[at] ?? 0) / total : 1);
  const settled = $derived(!isProvisional(agreed));
  const said = $derived(
    total
      ? verdict(breakdown, periods, at)
      : {
          title: 'No delay recorded',
          detail: `Nothing was picked up ${where} this month.`
        }
  );
  const records = $derived(
    (
      [
        ['nr', "Network Rail's own causes"],
        ['op', "the operators' causes"]
      ] as const
    ).flatMap(([side, name]) => {
      const ids = groups.filter((g) => g.side === side).map((g) => g.id);
      if (!isRecord(breakdown, periods, at, ids)) return [];
      const a = minutes(perDay(breakdown, periods, at, ids));
      return [`Delay from ${name} was the highest since ${since}, at ${a} minutes a day.`];
    })
  );
</script>

<section class="info sign" aria-labelledby="info-title">
  <div class="head">
    <p class="when">{spanLong(period)}</p>
    <svelte:element this={main ? 'h1' : 'h2'} id="info-title">{said.title}</svelte:element>
    <p class="detail">{said.detail}</p>
  </div>

  <div class="body">
    <dl class="rows">
      <div>
        <dt>Minutes of delay</dt>
        <dd class="big"><Rolling value={total} format={minutes} /></dd>
      </div>
      <div>
        <dt>Minutes a day</dt>
        <dd><Rolling value={day} format={minutes} /></dd>
      </div>
      <div>
        <dt>Trains cancelled</dt>
        <dd>{minutes(cancelled)}</dd>
      </div>
      <div>
        <dt>Knock-on from earlier delays</dt>
        <dd>{percent(knock)}</dd>
      </div>
    </dl>

    <div class="words">
      <p class="sentence">{summarise(breakdown, groups, at, where)}</p>
      {#each records as line (line)}
        <p class="record">{line}</p>
      {/each}
      <p class="plate" class:provisional={!settled}>
        <strong>{settled ? 'Mostly agreed' : 'Not final yet'}</strong>
        Network Rail and the operators had agreed on {percent(agreed)} of these minutes when the figures
        came out on {dateLong(period.released ?? period.end)}.{settled
          ? ''
          : ' The rest could still change.'}
      </p>
    </div>
  </div>

  {#if children}
    <div class="foot">{@render children()}</div>
  {/if}
</section>

<style>
  .info {
    display: grid;
    overflow: hidden;
  }

  .head {
    display: grid;
    gap: var(--space-2);
    padding: var(--space-5) var(--space-5) var(--space-4);
    border-bottom: 1px solid var(--sign-rule);

    h1,
    h2 {
      font-size: var(--step-3);
      max-width: 20ch;
    }
  }

  .when {
    color: var(--edge);
    font-weight: 800;
    font-size: var(--step-0);
  }

  .detail {
    color: var(--on-sign-muted);
    font-size: var(--step-1);
    max-width: 44ch;
  }

  .body {
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  }

  .rows {
    margin: 0;

    div {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: var(--space-4);
      padding: var(--space-3) var(--space-5);
      border-bottom: 1px solid var(--sign-rule);
    }

    div:last-child {
      border-bottom: 0;
    }

    dt {
      color: var(--on-sign-muted);
      font-weight: 600;
    }

    dd {
      margin: 0;
      font-size: var(--step-2);
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }

    .big {
      font-size: var(--step-figure);
      line-height: 1;
      letter-spacing: -0.03em;
    }
  }

  .words {
    display: grid;
    align-content: start;
    gap: var(--space-4);
    padding: var(--space-5);
    border-left: 1px solid var(--sign-rule);
  }

  .sentence {
    font-size: var(--step-1);
    line-height: 1.4;
    font-weight: 600;
  }

  .record {
    color: var(--on-sign-muted);
  }

  .plate {
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius);
    background: var(--sign-raised);
    font-size: var(--step--1);

    strong {
      display: block;
      font-size: var(--step-0);
    }

    &.provisional {
      background: var(--edge);
      color: var(--sign);
    }
  }

  .foot {
    padding: var(--space-4) var(--space-5);
    border-top: 1px solid var(--sign-rule);
    color: var(--on-sign-muted);
  }

  @media (max-width: 52rem) {
    .body {
      grid-template-columns: minmax(0, 1fr);
    }

    .words {
      border-left: 0;
      border-top: 1px solid var(--sign-rule);
    }
  }

  @media (max-width: 30rem) {
    .head,
    .words,
    .foot {
      padding-inline: var(--space-4);
    }

    .rows div {
      padding-inline: var(--space-4);
    }
  }
</style>
