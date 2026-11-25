import { getJson, type Index } from '#lib/data.ts';

export const prerender = true;
export const trailingSlash = 'never';

export const load = async ({ fetch }) => ({
  index: await getJson<Index>(fetch, '/data/index.json')
});
