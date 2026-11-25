import { getJson, type Odd } from '#lib/data.ts';

export const load = async ({ fetch }) => ({ odd: await getJson<Odd>(fetch, '/data/odd.json') });
