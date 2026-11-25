import { describe, expect, it } from 'vitest';
import { describeStanding, siblings, standing, summarise } from '../src/lib/compare.ts';
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
  const p = { ...period('2023-24-P08'), end: '2023-11-11' };

  it('says most only when one cause is over half', () => {
    expect(summarise(breakdown(60, 40), groups, p, 0, 'at Tonbridge')).toBe(
      'Most of the delay picked up at Tonbridge in the four weeks to 11 November 2023 came from autumn leaves.'
    );
  });

  it('names the biggest share otherwise', () => {
    expect(summarise(breakdown(40, 35, 25), groups, p, 0, 'at Tonbridge')).toContain(
      'The biggest share (40%) of the delay'
    );
  });
});
