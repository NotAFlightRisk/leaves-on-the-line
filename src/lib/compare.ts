import type { Breakdown, Group, Period, Series } from './data.ts';
import { phrases } from './causes.ts';
import { count, dateMonth, list, monthName, months, percent } from './format.ts';

// lockdown timetables make 2020-21 a poor yardstick for any other year
const SKIPPED_YEAR = '2020-21';

/** Network Rail's year has 13 four-week periods, which the site calls months */
export const PERIODS_A_YEAR = 13;

/** Below this share of minutes agreed, a month's figures could still move */
const SETTLED = 0.94;

export const isProvisional = (agreed: number | null) => (agreed ?? 1) < SETTLED;

export const sum = (values: (number | null)[]) => values.reduce<number>((a, v) => a + (v ?? 0), 0);

export const share = (part: number, whole: number) => (whole > 0 ? part / whole : 0);

export function totalAt(breakdown: Breakdown, at: number) {
  return sum(Object.values(breakdown.minutes).map((series) => series[at] ?? null));
}

/** Delay minutes a day for the given causes, or all of them, in one period */
export function perDay(breakdown: Breakdown, periods: Period[], at: number, ids?: string[]) {
  const picked = ids ?? Object.keys(breakdown.minutes);
  return sum(picked.map((id) => breakdown.minutes[id]?.[at] ?? null)) / periods[at].days;
}

/** The same period number in other years that has figures, by default a file */
export function siblings(periods: Period[], at: number, has = (i: number) => !!periods[i].file) {
  const number = periods[at].id.slice(-3);
  return periods.flatMap((p, i) =>
    i !== at && has(i) && p.id.endsWith(number) && !p.id.startsWith(SKIPPED_YEAR) ? [i] : []
  );
}

export type Standing = {
  perDay: number;
  low: number;
  high: number;
  years: number;
  above: number;
};

/** Where a period sits among the same period in other years, per day since lengths vary */
export function standing(series: Series, periods: Period[], at: number): Standing | null {
  const value = series[at];
  if (value == null) return null;
  const others = siblings(periods, at)
    .filter((i) => i < series.length)
    .map((i) => (series[i] ?? 0) / periods[i].days);
  if (others.length < 2) return null;
  const perDay = value / periods[at].days;
  return {
    perDay,
    low: Math.min(...others),
    high: Math.max(...others),
    years: others.length,
    above: others.filter((v) => perDay > v).length
  };
}

export function describeStanding(s: Standing) {
  if (s.above === s.years) return `the most in ${s.years + 1} years`;
  if (s.above === 0) return `the least in ${s.years + 1} years`;
  return `more than ${s.above} of the other ${s.years} years`;
}

/** The sentence a commuter reads first: which cause did the most */
export function summarise(breakdown: Breakdown, groups: Group[], at: number, where: string) {
  const total = totalAt(breakdown, at);
  if (!total) return `No delay was picked up ${where} this month.`;
  const [top] = groups
    .map((g) => ({ g, minutes: breakdown.minutes[g.id]?.[at] ?? 0 }))
    .sort((a, b) => b.minutes - a.minutes);
  const portion = share(top.minutes, total);
  return portion > 0.5
    ? `Most of it, ${percent(portion)}, came from ${phrases[top.g.id]}.`
    : `The biggest cause was ${phrases[top.g.id]}, at ${percent(portion)} of the total.`;
}

/** The periods we have a file for, which a ranking or a record can count */
const filed = (breakdown: Breakdown, periods: Period[]) =>
  periods.flatMap((p, i) => (p.file && i < breakdown.knock.length ? [i] : []));

/** True when these causes ran higher a day than in any other period on file */
export function isRecord(breakdown: Breakdown, periods: Period[], at: number, ids: string[]) {
  const mine = perDay(breakdown, periods, at, ids);
  return (
    mine > 0 &&
    filed(breakdown, periods).every((i) => i === at || perDay(breakdown, periods, i, ids) < mine)
  );
}

/** One month set against every other month on file */
type Comparison = {
  periods: Period[];
  at: number;
  others: number[];
  worse: number[];
  quieter: number[];
  /** true when the month is told by how quiet it was, not how bad */
  quiet: boolean;
  /** the months that beat it: worse ones, or quieter ones for a quiet month */
  beaten: number[];
  since: string;
};

/** A short headline for how a month compares, and a plain line that backs it up */
export function verdict(breakdown: Breakdown, periods: Period[], at: number) {
  const day = (i: number) => perDay(breakdown, periods, i);
  const mine = day(at);
  const others = filed(breakdown, periods).filter((i) => i !== at);
  const worse = others.filter((i) => day(i) > mine);
  const quieter = others.filter((i) => day(i) < mine);
  const quiet = quieter.length < worse.length;
  const c: Comparison = {
    periods,
    at,
    others,
    worse,
    quieter,
    quiet,
    beaten: quiet ? quieter : worse,
    since: dateMonth(periods[0].start)
  };
  return { title: headline(c), detail: backing(c) };
}

function headline({ periods, at, others, worse, quieter, quiet, beaten, since }: Comparison) {
  const worst = quiet ? 'quietest month' : 'worst month for delays';
  // count the months back to the last one that beat this one
  const last = beaten.filter((i) => i < at).at(-1);
  const gap = others.filter((i) => i < at && i > (last ?? -1)).length;
  if (gap >= 6) {
    return `The ${worst} since ${last == null ? since : sinceWhen(periods[last], periods[at])}`;
  }
  if (beaten.length <= 5) {
    const worstOnes = quiet ? 'quietest months' : 'worst months for delays';
    return `One of the ${worstOnes} since ${periods[0].start.slice(0, 4)}`;
  }
  if (worse.length <= others.length / 3) return 'Worse than most months';
  if (quieter.length <= others.length / 3) return 'Quieter than most months';
  return 'About a normal month';
}

/** "2019", or just "March" when it was earlier in the same year */
function sinceWhen(then: Period, now: Period) {
  const year = then.end.slice(0, 4);
  return year === now.end.slice(0, 4) ? monthName(then.end) : year;
}

function backing({ periods, at, others, worse, quieter, quiet, beaten, since }: Comparison) {
  const n = beaten.length;
  if (n === 0) {
    return `None of the other ${others.length} months since ${since} had as ${quiet ? 'little' : 'much'} delay a day.`;
  }
  if (n > 10) {
    return `${worse.length} of the ${others.length} other months since ${since} had more delay a day, and ${quieter.length} had less.`;
  }
  const only = `Only ${count(n)} ${n === 1 ? 'month' : 'months'} since ${since} had ${quiet ? 'less' : 'more'} delay a day`;
  if (n > 3) return `${only}.`;

  // a few months: say they were the same time of year, or name them
  const number = periods[at].id.slice(-3);
  if (beaten.every((i) => periods[i].id.endsWith(number))) {
    const all = n === 1 ? '' : n === 2 ? 'both ' : 'all ';
    return `${only}, ${all}this time of year in ${list(beaten.map((i) => periods[i].end.slice(0, 4)))}.`;
  }
  return `${only}: ${list(beaten.map((i) => months(periods[i])))}.`;
}
