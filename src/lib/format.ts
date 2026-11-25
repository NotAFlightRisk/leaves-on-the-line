type Span = { start: string; end: string };

const whole = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });
// the files give plain dates, so read them in UTC or a timezone can shift them a day
const dates = (options: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat('en-GB', { ...options, timeZone: 'UTC' });

const short = dates({ day: 'numeric', month: 'short', year: 'numeric' });
const long = dates({ day: 'numeric', month: 'long', year: 'numeric' });
const dayMonth = dates({ day: 'numeric', month: 'short' });
const dayMonthLong = dates({ day: 'numeric', month: 'long' });
const monthYear = dates({ month: 'long', year: 'numeric' });
const monthShortYear = dates({ month: 'short', year: 'numeric' });
const monthShort = dates({ month: 'short' });
const monthLong = dates({ month: 'long' });

export const minutes = (value: number | null | undefined) =>
  value == null ? '-' : whole.format(Math.round(value));

export const percent = (value: number) =>
  `${value > 0 && value < 0.01 ? '<1' : Math.round(value * 100)}%`;

const dateShort = (iso: string) => short.format(new Date(iso));

/** 9 December 2023 */
export const dateLong = (iso: string) => long.format(new Date(iso));

/** December 2023 */
export const dateMonth = (iso: string) => monthYear.format(new Date(iso));

/** December */
export const monthName = (iso: string) => monthLong.format(new Date(iso));

const sameYear = (p: Span) => p.start.slice(0, 4) === p.end.slice(0, 4);

/** 12 Nov to 9 Dec 2023, with both years when it straddles one */
export const span = (p: Span) =>
  `${sameYear(p) ? dayMonth.format(new Date(p.start)) : dateShort(p.start)} to ${dateShort(p.end)}`;

/** 12 November to 9 December 2023 */
export const spanLong = (p: Span) =>
  `${sameYear(p) ? dayMonthLong.format(new Date(p.start)) : dateLong(p.start)} to ${dateLong(p.end)}`;

/** Nov to Dec 2019, or just Apr 2020 when a period sits inside one month */
export function months(p: Span) {
  const [start, end] = [new Date(p.start), new Date(p.end)];
  if (p.start.slice(0, 7) === p.end.slice(0, 7)) return monthShortYear.format(end);
  const from = sameYear(p) ? monthShort.format(start) : monthShortYear.format(start);
  return `${from} to ${monthShortYear.format(end)}`;
}

const NUMBERS = [
  'no',
  'one',
  'two',
  'three',
  'four',
  'five',
  'six',
  'seven',
  'eight',
  'nine',
  'ten'
];

/** "no", "two" or "ten" in words, and 11 and up in digits */
export const count = (n: number) => NUMBERS[n] ?? String(n);

/** "2018 and 2019", "2018, 2019 and 2022" */
export const list = (items: string[]) =>
  items.length < 2 ? (items[0] ?? '') : `${items.slice(0, -1).join(', ')} and ${items.at(-1)}`;
