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
    font-weight: 800;
    font-size: var(--step-figure);
    line-height: 1;
    color: var(--text);
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.03em;
  }

  .unit {
    color: var(--text-muted);
    font-size: var(--step-1);
  }
</style>
