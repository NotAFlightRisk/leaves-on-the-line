<script lang="ts">
  import { page } from '$app/state';

  let { title, description }: { title: string; description: string } = $props();

  const full = $derived(title === 'Leaves on the Line' ? title : `${title} | Leaves on the Line`);
  const url = $derived(
    `https://leaves.peng.ly${page.url.pathname === '/' ? '' : page.url.pathname}`
  );
</script>

<svelte:head>
  <title>{full}</title>
  <meta name="description" content={description} />
  <link rel="canonical" href={url} />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="Leaves on the Line" />
  <meta property="og:title" content={full} />
  <meta property="og:description" content={description} />
  <meta property="og:url" content={url} />
  <meta property="og:image" content="https://leaves.peng.ly/og.png" />
  <meta name="twitter:card" content="summary_large_image" />
</svelte:head>
