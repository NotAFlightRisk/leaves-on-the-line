import { getJson, type Odd, type Trends } from '#lib/data.ts';

export const load = async ({ fetch }) => {
  const [odd, trends] = await Promise.all([
    getJson<Odd>(fetch, '/data/odd.json'),
    getJson<Trends>(fetch, '/data/trends.json')
  ]);
  return { odd, trends };
};
