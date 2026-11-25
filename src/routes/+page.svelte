<script lang="ts">
  import { untrack } from 'svelte';
  import { cause, covers, phrases, things } from '#lib/causes.ts';
  import { PERIODS_A_YEAR, share, siblings, sum } from '#lib/compare.ts';
  import { dateLong, dateMonth, minutes, months, percent, span, spanLong } from '#lib/format.ts';
  import ChartTip, { pointerIn } from '#lib/components/ChartTip.svelte';
  import History from '#lib/components/History.svelte';
  import Meta from '#lib/components/Meta.svelte';
  import Pictogram from '#lib/components/Pictogram.svelte';
  import Rolling from '#lib/components/Rolling.svelte';
  import Search from '#lib/components/Search.svelte';

  let { data } = $props();

  // the oddities with a pictogram, in the order they read best
  const ODD = ['swan', 'cow', 'balloon', 'trampoline', 'bird', 'tree'];
  // ORR's table puts autumn inside weather, so its weather row says so
  const ORR_WEATHER = {
    label: 'Weather, autumn and structures',
    covers: 'Storms, flooding, heat, snow, leaves on the line, and bridges, tunnels and earthworks'
  };

  const index = $derived(data.index);
  const periods = $derived(index.periods);
  const network = $derived(index.network);
  const orr = $derived(data.trends.orr);

  // Network Rail's own files stop at index.last, and ORR's figures carry on from the next month
  const handover = $derived(index.last + 1);
  const fromOrr = (i: number) => i >= handover;
  const has = (i: number) =>
    fromOrr(i) ? Object.values(orr).some((s) => s[i] != null) : !!periods[i].file;
  // ORR has no autumn series, so autumn reads as null in its months
  const value = (id: string, i: number) =>
    (fromOrr(i) ? orr[id]?.[i] : network.minutes[id]?.[i]) ?? null;
  const groupsAt = (i: number) =>
    fromOrr(i) ? index.groups.filter((g) => g.id !== 'autumn') : index.groups;
  const perDay = (i: number) => sum(index.groups.map((g) => value(g.id, i))) / periods[i].days;
  // the same month in every year, from the same source, so the two are never compared
  const sameMonth = (i: number) =>
    [...siblings(periods, i, (j) => has(j) && fromOrr(j) === fromOrr(i)), i].sort((a, b) => a - b);

  const latest = $derived(
    Math.max(index.last, ...Object.values(orr).map((s) => s.findLastIndex((v) => v != null)))
  );
  let at = $state(untrack(() => latest));

  // one set of figures for the chart, Network Rail's files then ORR's
  const merged = $derived({
    minutes: Object.fromEntries(
      index.groups.map((g) => [g.id, periods.slice(0, latest + 1).map((_, i) => value(g.id, i))])
    )
  });

  const period = $derived(periods[at]);
  const orrMonth = $derived(fromOrr(at));
  const day = $derived(perDay(at));
  const total = $derived(day * period.days);

  const yearAgo = $derived.by(() => {
    const i = at - PERIODS_A_YEAR;
    return i >= 0 && has(i) && fromOrr(i) === orrMonth ? i : null;
  });
  const before = $derived(yearAgo == null ? null : perDay(yearAgo));
  const change = $derived(before ? day / before - 1 : null);
  const title = $derived(
    change == null
      ? 'What held trains up'
      : change > 0.05
        ? 'More delay than this time last year'
        : change < -0.05
          ? 'Less delay than this time last year'
          : 'About the same delay as this time last year'
  );
  const versus = $derived.by(() => {
    if (yearAgo == null || before == null) return null;
    return {
      label: `${minutes(day)} a day this month, ${minutes(before)} a day a year earlier`,
      longest: Math.max(day, before),
      bars: [
        { when: months(period), value: day, now: true },
        { when: months(periods[yearAgo]), value: before, now: false }
      ]
    };
  });

  const rows = $derived(
    groupsAt(at).map((g) => {
      const v = value(g.id, at) ?? 0;
      const weather = orrMonth && g.id === 'weather';
      return {
        g,
        label: weather ? ORR_WEATHER.label : g.label,
        covers: weather ? ORR_WEATHER.covers : covers[g.id],
        value: v,
        day: v / period.days,
        portion: share(v, total),
        cancelled: orrMonth ? 0 : (network.cancelled[g.id]?.[at] ?? 0),
        years: sameMonth(at).map((i) => ({
          id: periods[i].id,
          when: months(periods[i]),
          value: (value(g.id, i) ?? 0) / periods[i].days,
          mine: i === at
        }))
      };
    })
  );
  type Row = (typeof rows)[number];
  const biggest = $derived.by(() => {
    const [a, b] = [...rows].sort((x, y) => y.value - x.value);
    const lead = `The biggest cause was ${phrases[a.g.id]}, at ${percent(a.portion)}`;
    return b && a.portion - b.portion < 0.015
      ? `${lead}, with ${phrases[b.g.id]} close behind at ${percent(b.portion)}.`
      : `${lead} of the total.`;
  });
  const sides = $derived(
    (
      [
        ['nr', "Network Rail's causes"],
        ['op', "The operators' causes"]
      ] as const
    ).map(([side, heading]) => {
      const mine = rows.filter((r) => r.g.side === side).sort((a, b) => b.value - a.value);
      return { side, heading, rows: mine, portion: share(sum(mine.map((r) => r.value)), total) };
    })
  );
  // the operators' column has a row to spare when Network Rail's has more causes
  const uneven = $derived(sides[0].rows.length > sides[1].rows.length);
  // stripes share one scale, full width being the next 5% above the biggest cause
  const scale = $derived(
    Math.max(0.05, Math.ceil(Math.max(...rows.map((r) => r.portion)) * 20) / 20)
  );

  const odd = $derived(
    ODD.flatMap((word) => {
      const found = data.odd.words.find(([w]) => w === word);
      return found ? [{ word, incidents: found[1], value: found[2] }] : [];
    })
  );

  let board: HTMLElement;
  let boardWidth = $state(0);
  let tip: Row | null = $state(null);
  let pointer = $state({ x: 0, y: 0 });

  function show(event: PointerEvent, row: Row) {
    pointer = pointerIn(board, event);
    tip = row;
  }
</script>

<Meta
  title="Leaves on the Line"
  description="Why Britain's trains are late, cause by cause, for the whole network, every operator and every station, from Network Rail's and ORR's own delay records."
/>

<div class="home">
  <section class="hero" aria-labelledby="title">
    <div class="intro">
      <h1 id="title">Why are Britain's trains late?</h1>
      <p class="lede">
        We track the reason for every minute of delay on Britain's passenger trains.
      </p>
      <Search id="home-search" large label="Find your station" />
      <p class="aside">
        Station figures stop at {dateLong(periods[index.last].end)}, the last month Network Rail
        made public station by station.
      </p>
    </div>

    <section class="latest sign" aria-labelledby="latest">
      <p class="when">
        {at === latest ? 'Latest figures:' : 'Showing'}
        {spanLong(period)}
      </p>
      <h2 id="latest">{title}</h2>
      <p class="figure">
        <span class="big"><Rolling value={day} format={minutes} /></span>
        <span>minutes of delay a day, across all passenger trains</span>
      </p>
      {#if versus}
        <div class="versus" role="img" aria-label={versus.label}>
          {#each versus.bars as bar (bar.when)}
            <span class="when-label">{bar.when}</span>
            <span class="track">
              <span class:now={bar.now} style:width="{(bar.value / versus.longest) * 100}%"></span>
            </span>
            <span class="v">{minutes(bar.value)}</span>
          {/each}
        </div>
      {/if}
      <p class="sentence">{biggest}</p>
      <p class="small">
        {minutes(total)} minutes in the whole month.
        {#if orrMonth}
          ORR publishes these figures a few weeks after each month ends.
        {:else}
          These figures come from Network Rail's own delay files.
        {/if}
        {#if at !== latest}
          <button type="button" onclick={() => (at = latest)}>Back to the latest</button>
        {/if}
      </p>
    </section>
  </section>

  <section class="causes" aria-labelledby="causes" bind:this={board} bind:clientWidth={boardWidth}>
    <h2 id="causes">What held trains up, {span(period)}</h2>
    {#each sides as s (s.side)}
      <div class="side sign {s.side}">
        <h3 class="dir">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d={s.side === 'nr' ? 'M21 12H4M10 5l-7 7 7 7' : 'M3 12h17M14 5l7 7-7 7'} />
          </svg>
          <span class="title">{s.heading}</span>
          <span class="portion">{percent(s.portion)}</span>
        </h3>
        <ol>
          {#each s.rows as r (r.g.id)}
            <li class:empty={!r.value}>
              <span class="pict"><Pictogram name={r.g.id} /></span>
              <span class="what">
                <span class="name">{r.label}</span>
                <span class="covers">{r.covers}</span>
              </span>
              <span class="figs">
                <span class="mins"><Rolling value={r.value} format={minutes} /></span>
                <span class="pct">{percent(r.portion)} of all delay</span>
                {#if r.cancelled}
                  <span class="pct">{minutes(r.cancelled)} trains cancelled</span>
                {/if}
              </span>
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <span
                class="stripe"
                aria-hidden="true"
                onpointermove={(e) => show(e, r)}
                onpointerleave={() => (tip = null)}
              >
                <span class="track">
                  <span
                    style:width="{Math.min(r.portion / scale, 1) * 100}%"
                    style:background={cause(r.g.id)}
                  ></span>
                </span>
              </span>
            </li>
          {/each}
          {#if s.side === 'op' && uneven}
            <li class="more">
              <span class="pict"><Pictogram name="next" /></span>
              <span class="what">
                <a class="name" href="#operators">Each operator</a>
                <span class="covers">
                  How each of the {index.operators.length} train companies did
                </span>
              </span>
            </li>
          {/if}
        </ol>
      </div>
    {/each}
    <p class="scale">
      A full stripe is {percent(scale)} of all delay. Hover over one to compare the same month in other
      years.
      {#if orrMonth}
        These are ORR's figures, which count a few things differently from the station pages. <a
          href="/method#recent"
        >
          Here's how.
        </a>
      {:else}
        Delay involving people, like trespass or someone taken ill, is left out.
      {/if}
    </p>
    <ChartTip show={tip != null} x={pointer.x} y={pointer.y} bounds={boardWidth}>
      {#if tip}
        <span class="tip-when">{tip.label}</span>
        <span class="tip-main">{minutes(tip.day)} minutes a day</span>
        <span>{percent(tip.portion)} of all delay. The same month in other years:</span>
        <ul class="tip-rows">
          {#each tip.years as y (y.id)}
            <li>
              <span
                class="chip"
                style:background={y.mine ? cause(tip.g.id) : 'var(--on-sign-muted)'}
              ></span>
              <span class:mine={y.mine}>{y.when}</span>
              <span class="value" class:mine={y.mine}>{minutes(y.value)}</span>
            </li>
          {/each}
        </ul>
        <span class="tip-hint">
          {orrMonth
            ? `Minutes a day. ORR's figures start in ${dateMonth(periods[handover].start)}.`
            : 'Minutes a day. 2020-21 is left out, as lockdown skews it.'}
        </span>
      {/if}
    </ChartTip>
  </section>

  <section class="history" aria-labelledby="history">
    <h2 id="history">Every month since {dateMonth(periods[0].start)}</h2>
    <History
      breakdown={merged}
      groups={index.groups}
      {periods}
      bind:at
      {handover}
      name="across the network"
    />
  </section>

  <section class="odd" aria-labelledby="odd">
    <h2 id="odd" class="band">
      The odd ones since {dateMonth(periods[0].start)}
      <a href="/odd">See them all</a>
    </h2>
    <ul>
      {#each odd as o (o.word)}
        <li>
          <span class="pict"><Pictogram name={o.word} /></span>
          <span class="label">{things[o.word]}</span>
          <span class="count">{minutes(o.incidents)} incidents</span>
          <span class="mins">{minutes(o.value)} minutes of delay</span>
        </li>
      {/each}
    </ul>
  </section>

  <nav class="directory sign" aria-label="Stations, routes, operators and more">
    <div>
      <h2>Routes</h2>
      <ul class="cols">
        {#each index.routes as route (route.id)}
          <li><a href="/route/{route.id}">{route.name}</a></li>
        {/each}
      </ul>
    </div>
    <div>
      <h2 id="operators">Operators</h2>
      <ul class="cols">
        {#each index.operators as op (op.id)}
          <li><a href="/operator/{op.id}">{op.name}</a></li>
        {/each}
      </ul>
    </div>
    <div>
      <h2>More</h2>
      <ul>
        <li><a href="/stations">All {minutes(index.stations)} stations</a></li>
        <li><a href="/map">The map</a>, where each cause starts</li>
        <li><a href="/trends">Trends</a> since 2018, storms and all</li>
        <li><a href="/odd">The odd ones</a></li>
        <li><a href="/method">How it's worked out</a></li>
      </ul>
    </div>
  </nav>
</div>

<style>
  .home {
    display: grid;
    gap: var(--space-7);
  }

  .hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
    gap: var(--space-6);
    align-items: center;
  }

  .intro {
    display: grid;
    gap: var(--space-4);

    h1 {
      font-size: clamp(2.4rem, 5.2vw, 4rem);
      line-height: 1;
      letter-spacing: -0.025em;
    }
  }

  .lede {
    font-size: var(--step-1);
    line-height: 1.45;
    max-width: 34ch;
  }

  .aside {
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: 44ch;
  }

  .latest {
    display: grid;
    gap: var(--space-3);
    padding: var(--space-5);
    border-bottom: 10px solid var(--edge);

    h2 {
      font-size: var(--step-2);
      max-width: 22ch;
    }
  }

  .when {
    color: var(--edge);
    font-weight: 800;
  }

  .figure {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--space-1) var(--space-3);
    color: var(--on-sign-muted);
  }

  .big {
    font-size: var(--step-figure);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.03em;
    color: var(--on-sign);
    font-variant-numeric: tabular-nums;
  }

  .versus {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: var(--space-2) var(--space-3);
    font-size: var(--step--1);
    font-variant-numeric: tabular-nums;

    .when-label {
      color: var(--on-sign-muted);
    }

    .track {
      display: block;
      height: 10px;
      background: var(--sign-raised);
      border-radius: 5px;
      overflow: hidden;

      span {
        display: block;
        height: 100%;
        background: var(--on-sign-muted);

        &.now {
          background: var(--edge);
        }
      }
    }

    .v {
      font-weight: 700;
      text-align: right;
    }
  }

  .sentence {
    font-size: var(--step-0);
    font-weight: 600;
  }

  .small {
    color: var(--on-sign-muted);
    font-size: var(--step--1);

    button {
      margin-left: var(--space-2);
      min-height: 2.25rem;
      padding: 0 var(--space-3);
      background: var(--edge);
      color: var(--sign);
      border: 0;
      border-radius: var(--radius);
      font-weight: 800;
      cursor: pointer;
    }
  }

  .causes {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: var(--space-2) var(--space-4);

    > h2 {
      grid-column: 1 / -1;
      font-size: var(--step-2);
      margin-bottom: var(--space-2);
    }
  }

  .side {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .dir {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-4) var(--space-5);
    font-size: var(--step-2);
    border-bottom: 4px solid var(--edge);

    svg {
      flex: none;
      width: 2.5rem;
      height: 2.5rem;
      fill: none;
      stroke: var(--edge);
      stroke-width: 2.6;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    .portion {
      margin-left: auto;
      font-size: var(--step-3);
      line-height: 1;
    }
  }

  .op .dir {
    flex-direction: row-reverse;

    .portion {
      margin-left: 0;
      margin-right: auto;
    }
  }

  .side ol {
    flex: 1;
    display: flex;
    flex-direction: column;
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .side li {
    display: grid;
    grid-template-columns: 3rem minmax(0, 1fr) auto;
    grid-template-areas: 'pict what figs' 'stripe stripe stripe';
    align-items: center;
    gap: var(--space-2) var(--space-4);
    padding: var(--space-4) var(--space-5) var(--space-1);
    border-bottom: 1px solid var(--sign-rule);

    &:last-child {
      border-bottom: 0;
    }

    &.empty {
      color: var(--on-sign-muted);
    }

    &.more {
      flex: 1;
      grid-template-areas: 'pict what';
      grid-template-columns: 3rem minmax(0, 1fr);
      padding-bottom: var(--space-4);
      background: var(--sign-raised);

      .pict {
        background: var(--edge);
      }

      .name {
        color: var(--on-sign);
        text-decoration-color: var(--edge);
      }
    }
  }

  .pict {
    display: block;
    grid-area: pict;
    width: 3rem;
    height: 3rem;
    padding: 0.5rem;
    border-radius: var(--radius-chip);
    background: var(--on-sign);
    color: var(--sign);
  }

  .what {
    grid-area: what;
    display: grid;
    gap: 0.1rem;
  }

  .name {
    font-weight: 800;
    font-size: var(--step-1);
    line-height: 1.15;
  }

  .covers {
    color: var(--on-sign-muted);
    font-size: var(--step--1);
    line-height: 1.35;
  }

  .figs {
    grid-area: figs;
    display: grid;
    justify-items: end;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  .mins {
    font-weight: 800;
    font-size: var(--step-2);
    line-height: 1.1;
  }

  .pct {
    color: var(--on-sign-muted);
    font-size: var(--step--1);
    line-height: 1.35;
  }

  .stripe {
    grid-area: stripe;
    display: block;
    padding-block: var(--space-3);
    cursor: crosshair;

    &:hover .track {
      outline: 2px solid var(--on-sign-muted);
      outline-offset: 2px;
    }
  }

  .stripe .track {
    display: block;
    height: 6px;
    background: var(--sign-raised);
    border-radius: 3px;
    overflow: hidden;

    span {
      display: block;
      height: 100%;
    }
  }

  .scale {
    grid-column: 1 / -1;
    color: var(--text-muted);
    font-size: var(--step--1);
    max-width: var(--measure);
  }

  .history {
    display: grid;
    gap: var(--space-4);

    h2 {
      font-size: var(--step-2);
    }
  }

  .odd {
    background: var(--panel);
    border-radius: var(--radius);
    overflow: hidden;

    ul {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
    }

    li {
      display: grid;
      justify-items: start;
      align-content: start;
      gap: 0.1rem;
      padding: var(--space-4);
      border-right: 1px solid var(--rule);

      .pict {
        grid-area: auto;
        margin-bottom: var(--space-2);
        background: var(--sign);
        color: var(--on-sign);
      }
    }

    .mins {
      font-size: var(--step--1);
      font-weight: 400;
      color: var(--text-muted);
    }
  }

  .band {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-2) var(--space-4);
    padding: var(--space-3) var(--space-5);
    background: var(--sign);
    color: var(--on-sign);
    font-size: var(--step-1);

    a {
      color: var(--on-sign);
      font-size: var(--step-0);
      font-weight: 600;
      text-decoration-color: var(--edge);
    }
  }

  .label {
    font-weight: 800;
    font-size: var(--step-1);
  }

  .count {
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .directory {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr) minmax(0, 0.9fr);
    gap: var(--space-6);
    padding: var(--space-5) var(--space-5) var(--space-6);
    border-top: 10px solid var(--edge);

    h2 {
      font-size: var(--step-1);
      padding-bottom: var(--space-2);
      margin-bottom: var(--space-3);
      border-bottom: 1px solid var(--sign-rule);
      scroll-margin-top: var(--space-5);
    }

    ul {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: var(--space-1);
      color: var(--on-sign-muted);
    }

    .cols {
      display: block;
      columns: 2;
      column-gap: var(--space-5);

      li {
        break-inside: avoid;
        padding-block: 0.15rem;
      }
    }

    a {
      font-weight: 600;
      text-decoration-color: rgb(255 255 255 / 0.35);

      &:hover {
        text-decoration-color: var(--edge);
      }
    }
  }

  @media (max-width: 60rem) {
    .hero,
    .causes {
      grid-template-columns: minmax(0, 1fr);
    }

    .odd ul {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .directory {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);

      > div:last-child {
        grid-column: 1 / -1;
      }
    }

    .dir svg {
      rotate: -90deg;
    }

    .op .dir {
      flex-direction: row;

      svg {
        rotate: 90deg;
      }

      .portion {
        margin-left: auto;
        margin-right: 0;
      }
    }
  }

  @media (max-width: 36rem) {
    .latest {
      padding: var(--space-4);
    }

    .directory {
      grid-template-columns: minmax(0, 1fr);
    }

    .dir {
      padding-inline: var(--space-4);
    }

    .side li {
      grid-template-columns: 2.5rem minmax(0, 1fr);
      grid-template-areas: 'pict what' 'pict figs' 'stripe stripe';
      gap: var(--space-1) var(--space-3);
      padding-inline: var(--space-4);
    }

    .figs {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 0 var(--space-3);
    }

    .odd ul {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .pict {
      width: 2.5rem;
      height: 2.5rem;
      padding: 0.4rem;
    }

    .covers {
      display: none;
    }

    .more .covers {
      display: block;
    }
  }
</style>
