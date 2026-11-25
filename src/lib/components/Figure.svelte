<script lang="ts">
  import { cubicOut } from 'svelte/easing';
  import { untrack } from 'svelte';
  import { Tween } from 'svelte/motion';
  import { MediaQuery } from 'svelte/reactivity';
  import { minutes } from '#lib/format.ts';

  let { value, unit }: { value: number; unit: string } = $props();

  const calm = new MediaQuery('prefers-reduced-motion: reduce');
  // starts where the page was drawn, so it only rolls when the period changes
  const shown = new Tween(
    untrack(() => value),
    { easing: cubicOut }
  );

  $effect(() => {
    shown.set(value, { duration: calm.current ? 0 : 650 });
  });
</script>

<p class="figure">
  <span class="digits" aria-hidden="true">{minutes(shown.current)}</span>
  <span class="visually-hidden">{minutes(value)}</span>
  <span class="unit">{unit}</span>
</p>

<style>
  .figure {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--space-2) var(--space-4);
  }

  .digits {
    font-family: var(--font-board);
    font-weight: 700;
    font-size: var(--step-figure);
    line-height: 1;
    color: var(--figure);
    text-shadow: 0 0 0.35em var(--figure-glow);
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.02em;
  }

  .unit {
    color: var(--text-muted);
    font-size: var(--step-1);
  }
</style>
