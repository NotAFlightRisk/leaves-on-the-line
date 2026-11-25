<script lang="ts">
  import { slug } from '#lib/data.ts';
  import Meta from '#lib/components/Meta.svelte';
  import PlacePage from '#lib/components/PlacePage.svelte';

  let { data } = $props();

  const place = $derived(data.place);
  const route = $derived(data.index.routes.find((r) => r.id === slug(place.route ?? '')));
</script>

<Meta
  title="Why trains were late at {place.name}"
  description="What made passenger trains late at {place.name} ({place.crs}), cause by cause and month by month since 2018, from Network Rail's own delay records."
/>

<PlacePage
  {place}
  index={data.index}
  where="at {place.name}"
  counts="Delay that trains picked up at {place.name}, or on the stretch of line just after it. It isn't all the delay felt by people who travel from here, as trains can be held up before they arrive."
>
  {#snippet tags()}
    <span class="tag">{place.crs}</span>
    {#if route}<a class="tag" href="/route/{route.id}">{route.name} route</a>{/if}
  {/snippet}
</PlacePage>

<style>
  .tag {
    padding: var(--space-1) var(--space-3);
    border-radius: var(--radius);
    font-weight: 800;
    font-size: var(--step-0);
  }

  span.tag {
    background: var(--edge);
    color: var(--sign);
    letter-spacing: 0.04em;
  }

  a.tag {
    color: var(--on-sign);
    box-shadow: inset 0 0 0 2px var(--on-sign-muted);
    text-decoration: none;

    &:hover {
      box-shadow: inset 0 0 0 2px var(--edge);
    }
  }
</style>
