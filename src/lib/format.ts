const whole = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });
const short = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC'
});
const long = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC'
});

export const minutes = (value: number | null | undefined) =>
  value == null ? '-' : whole.format(Math.round(value));

export const percent = (value: number) =>
  `${value > 0 && value < 0.01 ? '<1' : Math.round(value * 100)}%`;

export const dateShort = (iso: string) => short.format(new Date(iso));
export const dateLong = (iso: string) => long.format(new Date(iso));

/** P09 2023-24 reads as the four weeks to 9 Dec 2023, which means something to everyone */
export const periodName = (period: { label: string; end: string }) =>
  `${period.label}, to ${dateShort(period.end)}`;
