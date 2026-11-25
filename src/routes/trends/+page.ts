import { getJson, type Trends } from '#lib/data.ts';

export const load = async ({ fetch }) => ({
  trends: await getJson<Trends>(fetch, '/data/trends.json')
});
