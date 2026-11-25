import type { Breakdown, Group, Period, Series } from './data.ts';
import { phrases } from './causes.ts';
import { dateLong, percent } from './format.ts';

// lockdown timetables make 2020-21 a poor yardstick for any other year
const SKIPPED_YEAR = '2020-21';

export type Standing = {
  perDay: number;
  low: number;
  high: number;
  years: number;
  above: number;
};

export const sum = (values: (number | null)[]) => values.reduce<number>((a, v) => a + (v ?? 0), 0);

export function totalAt(breakdown: Breakdown, at: number) {
  return sum(Object.values(breakdown.minutes).map((series) => series[at] ?? null));
}

/** The same period number in other years we have a file for */
export function siblings(periods: Period[], at: number) {
  const number = periods[at].id.slice(-3);
  return periods.flatMap((p, i) =>
    i !== at && p.file && p.id.endsWith(number) && !p.id.startsWith(SKIPPED_YEAR) ? [i] : []
  );
}

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

export const share = (part: number, whole: number) => (whole > 0 ? part / whole : 0);

/** The sentence a commuter reads first */
export function summarise(
  breakdown: Breakdown,
  groups: Group[],
  period: Period,
  at: number,
  where: string
) {
  const total = totalAt(breakdown, at);
  if (!total)
    return `No delay was picked up ${where} in the four weeks to ${dateLong(period.end)}.`;
  const [top] = groups
    .map((g) => ({ g, minutes: breakdown.minutes[g.id]?.[at] ?? 0 }))
    .sort((a, b) => b.minutes - a.minutes);
  const portion = share(top.minutes, total);
  const lead = portion > 0.5 ? 'Most' : `The biggest share (${percent(portion)})`;
  return `${lead} of the delay picked up ${where} in the four weeks to ${dateLong(period.end)} came from ${phrases[top.g.id]}.`;
}

export function knockOnLine(breakdown: Breakdown, at: number) {
  const total = totalAt(breakdown, at);
  const knock = breakdown.knock[at] ?? 0;
  if (!total) return '';
  return `${percent(share(knock, total))} of these minutes were knock-on from something that happened elsewhere first.`;
}
