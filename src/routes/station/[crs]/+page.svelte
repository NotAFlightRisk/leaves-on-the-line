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
  description="What made passenger trains late at {place.name} ({place.crs}), cause by cause and period by period since 2018, from Network Rail's own delay records."
/>

<PlacePage
  {place}
  index={data.index}
  where="at {place.name}"
  counts="Delay picked up at {place.name} or on the run from it to the next timing point, which is where Network Rail recorded it. That's where the incident was only for the train it hit first, and about half is at the station itself while a fifth is on runs of 10 km or more. It's not the delay felt by everyone who travels from here."
>
  {#snippet tags()}
    <span class="tag">{place.crs}</span>
    {#if route}<a class="tag" href="/route/{route.id}">{route.name} route</a>{/if}
  {/snippet}
</PlacePage>

<style>
  .tag {
    padding: var(--space-1) var(--space-3);
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius);
    font-size: var(--step--1);
    font-weight: 700;
    letter-spacing: 0.04em;
  }

  span.tag {
    color: var(--figure);
  }
</style>
