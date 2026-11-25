import { getJson, type Place } from '#lib/data.ts';

export const load = async ({ fetch, params }) => ({
  place: await getJson<Place>(fetch, `/route/${params.id}.json`)
});
