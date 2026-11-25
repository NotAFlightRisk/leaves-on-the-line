import { describe, expect, it } from 'vitest';
import { count, list, monthName, months, span, spanLong } from '../src/lib/format.ts';

describe('dates', () => {
  it('reads a month as its dates, with one year when both ends share it', () => {
    expect(span({ start: '2023-11-12', end: '2023-12-09' })).toBe('12 Nov to 9 Dec 2023');
    expect(spanLong({ start: '2023-11-12', end: '2023-12-09' })).toBe(
      '12 November to 9 December 2023'
    );
  });

  it('gives both years when a month straddles new year', () => {
    expect(span({ start: '2023-12-10', end: '2024-01-06' })).toBe('10 Dec 2023 to 6 Jan 2024');
  });

  it('names the calendar months a period touches', () => {
    expect(months({ start: '2019-11-10', end: '2019-12-07' })).toBe('Nov to Dec 2019');
    expect(months({ start: '2020-04-01', end: '2020-04-25' })).toBe('Apr 2020');
    expect(months({ start: '2023-12-10', end: '2024-01-06' })).toBe('Dec 2023 to Jan 2024');
  });

  it('reads plain dates in UTC, so a timezone never shifts the day', () => {
    expect(monthName('2024-03-01')).toBe('March');
  });
});

describe('words', () => {
  it('spells out small numbers', () => {
    expect([0, 1, 10, 11].map(count)).toEqual(['no', 'one', 'ten', '11']);
  });

  it('joins a list the way a sentence does', () => {
    expect(list([])).toBe('');
    expect(list(['2018'])).toBe('2018');
    expect(list(['2018', '2019'])).toBe('2018 and 2019');
    expect(list(['2018', '2019', '2022'])).toBe('2018, 2019 and 2022');
  });
});
