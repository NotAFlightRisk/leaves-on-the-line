import { describe, expect, it } from 'vitest';
import { describeStanding, siblings, standing, summarise, verdict } from '../src/lib/compare.ts';
import type { Breakdown, Group, Period } from '../src/lib/data.ts';

const period = (id: string, days = 28, file: string | null = 'x.zip'): Period => ({
  id,
  label: id,
  start: '2020-01-01',
  end: '2020-01-28',
  days,
  file,
  released: '2020-02-01',
  agreed: 0.97
});

const periods = [
  period('2018-19-P08'),
  period('2019-20-P08'),
  period('2020-21-P08'),
  period('2021-22-P08', 28, null),
  period('2022-23-P08', 14),
  period('2023-24-P08'),
  period('2023-24-P09')
];

describe('standing', () => {
  it('compares with the same period in other years, leaving out 2020-21 and gaps', () => {
    expect(siblings(periods, 5)).toEqual([0, 1, 4]);
  });

  it('can count other figures than a file, like ORR months', () => {
    expect(siblings(periods, 5, (i) => i !== 0)).toEqual([1, 3, 4]);
  });

  it('reads every year per day, since period lengths differ', () => {
    const series = [280, 560, 9999, null, 280, 840, 0];
    expect(standing(series, periods, 5)).toEqual({
      perDay: 30,
      low: 10,
      high: 20,
      years: 3,
      above: 3
    });
  });

  it('says where a year sits without a percentage', () => {
    const s = standing([280, 560, 0, null, 280, 420, 0], periods, 5)!;
    expect(describeStanding(s)).toBe('more than 1 of the other 3 years');
  });

  it('gives up with fewer than two other years', () => {
    expect(standing([1, 1, 1, 1, 1, 1, 1], periods.slice(4), 1)).toBeNull();
  });
});

describe('summarise', () => {
  const groups: Group[] = [
    { id: 'autumn', label: 'Autumn', orr: '', side: 'nr' },
    { id: 'fleet', label: 'Train faults', orr: '', side: 'op' },
    { id: 'track', label: 'Track', orr: '', side: 'nr' }
  ];
  const breakdown = (autumn: number, fleet: number, track = 0): Breakdown => ({
    minutes: { autumn: [autumn], fleet: [fleet], track: [track] },
    cancelled: {},
    unagreed: [0],
    knock: [0],
    codes: { latest: [], all: [] }
  });
  it('says most only when one cause is over half', () => {
    expect(summarise(breakdown(60, 40), groups, 0, 'at Tonbridge')).toBe(
      'Most of it, 60%, came from autumn leaves.'
    );
  });

  it('names the biggest cause otherwise', () => {
    expect(summarise(breakdown(40, 35, 25), groups, 0, 'at Tonbridge')).toBe(
      'The biggest cause was autumn leaves, at 40% of the total.'
    );
  });

  it('says when there was no delay at all', () => {
    expect(summarise(breakdown(0, 0), groups, 0, 'at Tonbridge')).toBe(
      'No delay was picked up at Tonbridge this month.'
    );
  });
});

describe('verdict', () => {
  // three years of four-week periods from April 2018, quiet except for the given ones
  const months = Array.from({ length: 36 }, (_, i): Period => {
    const start = new Date(Date.UTC(2018, 3, 1) + i * 28 * 86400000);
    const end = new Date(start.getTime() + 27 * 86400000);
    const year = 2018 + Math.floor(i / 13);
    return {
      ...period(`${year}-${String(year + 1).slice(2)}-P${String((i % 13) + 1).padStart(2, '0')}`),
      start: start.toISOString().slice(0, 10),
      end: end.toISOString().slice(0, 10)
    };
  });
  const delay = (busy: Record<number, number>): Breakdown => ({
    minutes: { track: months.map((_, i) => (busy[i] ?? 10 + (i % 7)) * 28) },
    cancelled: {},
    unagreed: months.map(() => 0),
    knock: months.map(() => 0),
    codes: { latest: [], all: [] }
  });

  it('counts back to the last worse month, and spots the same time of year', () => {
    expect(verdict(delay({ 8: 50, 21: 60, 34: 45 }), months, 34)).toEqual({
      title: 'The worst month for delays since 2019',
      detail:
        'Only two months since April 2018 had more delay a day, both this time of year in 2018 and 2019.'
    });
  });

  it('names the month when the last worse one was earlier the same year', () => {
    expect(verdict(delay({ 22: 60, 30: 50 }), months, 30).title).toBe(
      'The worst month for delays since January'
    );
  });

  it('says so when nothing was worse', () => {
    expect(verdict(delay({ 34: 99 }), months, 34)).toEqual({
      title: 'The worst month for delays since April 2018',
      detail: 'None of the other 35 months since April 2018 had as much delay a day.'
    });
  });

  it('still says it was one of the worst when the last worse month was recent', () => {
    expect(verdict(delay({ 30: 70, 33: 60 }), months, 33).title).toBe(
      'One of the worst months for delays since 2018'
    );
  });

  it('uses words in the middle, where counting back means little', () => {
    expect(verdict(delay({}), months, 31).title).toBe('About a normal month');
  });
});
