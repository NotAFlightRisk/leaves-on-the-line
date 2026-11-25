import { getJson, type Index } from '#lib/data.ts';

export const prerender = true;

const SITE = 'https://leaves.peng.ly';

export async function GET({ fetch }) {
  const index = await getJson<Index>(fetch, '/data/index.json');
  const stations = await getJson<[string, string, number][]>(fetch, '/data/stations.json');
  const paths = [
    '',
    '/stations',
    '/map',
    '/trends',
    '/odd',
    '/method',
    ...index.routes.map((r) => `/route/${r.id}`),
    ...index.operators.map((o) => `/operator/${o.id}`),
    ...stations.map(([crs]) => `/station/${crs}`)
  ];
  const urls = paths.map((path) => `<url><loc>${SITE}${path}</loc></url>`).join('');
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`,
    { headers: { 'Content-Type': 'application/xml' } }
  );
}
