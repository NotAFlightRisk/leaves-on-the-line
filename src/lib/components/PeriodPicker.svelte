<script lang="ts">
  import type { Period } from '#lib/data.ts';
  import { span } from '#lib/format.ts';

  let { periods, at = $bindable() }: { periods: Period[]; at: number } = $props();

  const choices = $derived(periods.flatMap((p, i) => (p.file ? [i] : [])));
  const place = $derived(choices.indexOf(at));
</script>

<div class="picker">
  <button
    type="button"
    aria-label="Previous month"
    disabled={place <= 0}
    onclick={() => (at = choices[place - 1])}
  >
    <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3 5 8l5 5" /></svg>
  </button>
  <label class="select">
    <span class="visually-hidden">Month</span>
    <select bind:value={at}>
      {#each choices as i (i)}
        <option value={i}>{span(periods[i])}</option>
      {/each}
    </select>
  </label>
  <button
    type="button"
    aria-label="Next month"
    disabled={place >= choices.length - 1}
    onclick={() => (at = choices[place + 1])}
  >
    <svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5" /></svg>
  </button>
</div>

<style>
  .picker {
    display: inline-flex;
    align-items: stretch;
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius);
    background: var(--panel);
  }

  select {
    height: 100%;
    border: 0;
    border-inline: 1px solid var(--rule-strong);
    border-radius: 0;
  }

  button {
    min-width: 2.5rem;
    background: none;
    border: 0;
    cursor: pointer;

    svg {
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 1.75;
      stroke-linecap: round;
      stroke-linejoin: round;
    }

    &:hover:not(:disabled) {
      color: var(--figure);
    }

    &:disabled {
      color: var(--text-faint);
      cursor: default;
    }
  }

  @media (max-width: 30rem) {
    .picker {
      display: flex;
      width: 100%;
    }

    .select {
      flex: 1;
      min-width: 0;
    }

    select {
      min-width: 0;
      text-overflow: ellipsis;
      font-size: var(--step--1);
    }

    button {
      min-width: 2.25rem;
    }
  }
</style>
