import { getJson } from '#lib/data.ts';

export const load = async ({ fetch }) => ({
  stations: await getJson<[crs: string, name: string, minutes: number][]>(
    fetch,
    '/data/stations.json'
  )
});
