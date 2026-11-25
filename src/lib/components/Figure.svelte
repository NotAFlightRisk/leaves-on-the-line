<script lang="ts">
  import { minutes } from '#lib/format.ts';
  import Rolling from './Rolling.svelte';

  let { value, unit }: { value: number; unit: string } = $props();
</script>

<p class="figure">
  <span class="digits"><Rolling {value} format={minutes} /></span>
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
