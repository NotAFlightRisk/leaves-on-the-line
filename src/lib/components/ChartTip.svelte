<script lang="ts" module>
  /** Where the pointer is, in px from the top left of the box the tip is placed in */
  export function pointerIn(box: HTMLElement, event: MouseEvent) {
    const rect = box.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }
</script>

<script lang="ts">
  import type { Snippet } from 'svelte';

  /** x and y are the pointer, in px from the nearest positioned box, and tall tips sit beside it */
  let {
    show,
    x,
    y,
    bounds,
    beside = false,
    children
  }: {
    show: boolean;
    x: number;
    y: number;
    bounds: number;
    beside?: boolean;
    children: Snippet;
  } = $props();

  const GAP = 14;

  let width = $state(0);
  let height = $state(0);
  // slide between spots once it's showing, but appear in place the first time
  let gliding = $state(false);

  const left = $derived(
    beside
      ? x + GAP + width <= bounds
        ? x + GAP
        : Math.max(0, x - GAP - width)
      : Math.max(0, Math.min(x - width / 2, bounds - width))
  );
  const top = $derived(
    beside
      ? Math.max(-height / 3, y - height / 2)
      : y - height - GAP < -8
        ? y + GAP + 6
        : y - height - GAP
  );

  $effect(() => {
    if (!show) {
      gliding = false;
      return;
    }
    const frame = requestAnimationFrame(() => (gliding = true));
    return () => cancelAnimationFrame(frame);
  });
</script>

<div
  class="chart-tip"
  class:show
  class:gliding
  aria-hidden="true"
  bind:offsetWidth={width}
  bind:offsetHeight={height}
  style:translate="{left}px {top}px"
>
  {@render children()}
</div>

<style>
  .chart-tip {
    position: absolute;
    left: 0;
    top: 0;
    z-index: 20;
    width: max-content;
    min-width: 11rem;
    max-width: min(19rem, 90vw);
    padding: var(--space-3) var(--space-4);
    background: var(--sign);
    color: var(--on-sign);
    border-radius: var(--radius);
    box-shadow:
      var(--shadow),
      0 0 0 1px rgb(255 255 255 / 0.08) inset;
    font-size: 0.875rem;
    line-height: 1.4;
    pointer-events: none;
    opacity: 0;
    transition: opacity 120ms ease-out;
  }

  .show {
    opacity: 1;
  }

  .gliding {
    transition:
      opacity 120ms ease-out,
      translate 110ms cubic-bezier(0.2, 0.7, 0.3, 1);
  }

  @media (prefers-reduced-motion: reduce) {
    .chart-tip,
    .gliding {
      transition: none;
    }
  }
</style>
