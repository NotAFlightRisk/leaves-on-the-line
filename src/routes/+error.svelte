<script lang="ts">
  import { page } from '$app/state';

  const lost = $derived(page.status === 404);
</script>

<svelte:head>
  <title>{lost ? 'Not found' : 'Something broke'} | Leaves on the Line</title>
</svelte:head>

<section>
  <p class="code" aria-hidden="true">{page.status}</p>
  <h1>{lost ? "There's no train from here" : 'Something broke'}</h1>
  <p>
    {#if lost}
      That page isn't on the board. Stations go by their three-letter code, like
      <a href="/station/pad">/station/pad</a>, or try <a href="/stations">every station</a>.
    {:else}
      The page fell over while loading. Try again in a minute, or head back to
      <a href="/">the start</a>.
    {/if}
  </p>
</section>

<style>
  section {
    display: grid;
    gap: var(--space-4);
    max-width: var(--measure);
    padding-block: var(--space-7);
  }

  .code {
    justify-self: start;
    padding: var(--space-2) var(--space-5);
    background: var(--sign);
    color: var(--edge);
    border-radius: var(--radius);
    font-weight: 800;
    font-size: var(--step-figure);
    font-variant-numeric: tabular-nums;
    line-height: 1;
  }

  h1 {
    font-size: var(--step-3);
  }
</style>
