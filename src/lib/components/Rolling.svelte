<script lang="ts">
  import { untrack } from 'svelte';
  import { cubicOut } from 'svelte/easing';
  import { Tween } from 'svelte/motion';
  import { MediaQuery } from 'svelte/reactivity';

  let { value, format }: { value: number; format: (value: number) => string } = $props();

  const calm = new MediaQuery('prefers-reduced-motion: reduce');
  const shown = new Tween(
    untrack(() => value),
    { easing: cubicOut }
  );

  $effect(() => {
    shown.set(value, { duration: calm.current ? 0 : 650 });
  });
</script>

<span aria-hidden="true">{format(shown.current)}</span><span class="visually-hidden">
  {format(value)}
</span>
