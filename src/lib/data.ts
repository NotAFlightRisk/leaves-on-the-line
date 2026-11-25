import { error } from '@sveltejs/kit';

export type Series = (number | null)[];
export type Code = [code: string, description: string, minutes: number];
export type Responsible = 'self' | 'nr' | 'other';

export type Period = {
  id: string;
  label: string;
  start: string;
  end: string;
  days: number;
  file: string | null;
  released: string | null;
  agreed: number | null;
};

export type Group = { id: string; label: string; orr: string; side: 'nr' | 'op' };

export type Breakdown = {
  minutes: Record<string, Series>;
  cancelled: Record<string, Series>;
  unagreed: Series;
  knock: Series;
  codes: { latest: Code[]; all: Code[] };
};

export type Link = { id: string; name: string };

export type Index = {
  periods: Period[];
  last: number;
  stations: number;
  taken: Record<'naptan' | 'network-rail' | 'orr', string>;
  groups: Group[];
  routes: Link[];
  operators: Link[];
  network: Breakdown & { total: Series; responsible: Record<Responsible, Series> };
};

export type Place = Breakdown & {
  kind: 'station' | 'route' | 'operator';
  id: string;
  name: string;
  crs?: string;
  route?: string;
  lat?: number;
  lon?: number;
  quiet?: boolean;
  former?: string[];
  responsible?: Record<Responsible, Series>;
  orr?: Record<string, Series>;
  sections?: Record<string, [name: string, minutes: number][]>;
};

export type Trends = {
  people: Series;
  orr: Record<string, Series>;
  worst: [day: string, minutes: number, by: Record<string, number>][];
  storms: [day: string, minutes: number, by: Record<string, number>][];
};

export type Odd = {
  codes: [code: string, description: string, incidents: number, minutes: number][];
  words: [word: string, incidents: number, minutes: number][];
};

export type Feature = [kind: 'line' | 'dot' | 'ring', name: string, ...coords: number[]];
export type MapPeriod = {
  m: [feature: number, group: number, minutes: number][];
  off: Record<string, number>;
};

type Fetch = typeof fetch;

export async function getJson<T>(fetch: Fetch, path: string): Promise<T> {
  const response = await fetch(path);
  if (response.status === 404) error(404, 'Not found');
  if (!response.ok) throw new Error(`${path} answered ${response.status}`);
  return response.json();
}

export const slug = (text: string) =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
