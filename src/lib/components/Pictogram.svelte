<script lang="ts" module>
  type Part = { d: string; cut?: boolean; line?: boolean };

  // solid shapes on a 48 grid like station signs, and cut parts punch holes
  const shapes: Record<string, Part[]> = {
    track: [{ d: 'M13 3h5v42h-5zM30 3h5v42h-5zM6 8h36v5H6zM6 21h36v5H6zM6 34h36v5H6z' }],
    assets: [
      {
        d: 'M24 2a9 9 0 0 1 9 9v14a9 9 0 0 1-18 0V11a9 9 0 0 1 9-9zM24 7a3.4 3.4 0 1 0 0 6.8A3.4 3.4 0 1 0 24 7zM24 14.6a3.4 3.4 0 1 0 0 6.8 3.4 3.4 0 1 0 0-6.8zM24 22.2a3.4 3.4 0 1 0 0 6.8 3.4 3.4 0 1 0 0-6.8z',
        cut: true
      },
      { d: 'M22 34h4v8h-4zM15 41h18v5H15z' }
    ],
    weather: [
      { d: 'M13 30a8 8 0 0 1-1-15.9A11.5 11.5 0 0 1 34.3 12 9 9 0 1 1 36 30z' },
      { d: 'M14 34h4.5l-3.5 10H10.5zM22 34h4.5l-3.5 10h-4.5zM30 34h4.5l-3.5 10h-4.5z' }
    ],
    autumn: [
      {
        d: 'M41 5C24 4 8 12 8 29c0 4 1 7 2.6 9.8L5 44.4 7.6 47l5.6-5.6C16 43 19.3 44 23 44 39 44 45 27 41 5zM13.5 38.6 35 15.4l1.2 1.1-21.5 23.2z',
        cut: true
      }
    ],
    external: [
      {
        d: 'M24 3 46 43H2zM21.8 16h4.4l-.8 15h-2.8zM24 34a2.7 2.7 0 1 1 0 5.4 2.7 2.7 0 0 1 0-5.4z',
        cut: true
      }
    ],
    network: [
      { d: 'M24 3a21 21 0 1 1 0 42 21 21 0 0 1 0-42zM22 10v15.5h12v-3.5h-8.5V10z', cut: true }
    ],
    fleet: [
      {
        d: 'M13 3h22a7 7 0 0 1 7 7v24a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V10a7 7 0 0 1 7-7zM11 9v12h26V9zM14 28.5a2.8 2.8 0 1 0 0 5.6 2.8 2.8 0 0 0 0-5.6zM34 28.5a2.8 2.8 0 1 0 0 5.6 2.8 2.8 0 0 0 0-5.6z',
        cut: true
      },
      { d: 'M12 41h5l-4 6H8zM31 41h5l4 6h-5z' }
    ],
    traincrew: [
      { d: 'M13 12.5C15 6 33 6 35 12.5l3 2.5H10z' },
      { d: 'M24 13a7.5 7.5 0 1 1 0 15 7.5 7.5 0 0 1 0-15z' },
      { d: 'M9 47c0-10 6.5-16 15-16s15 6 15 16z' }
    ],
    stations: [{ d: 'M24 3 46 15v5H2v-5zM7 20h5v20H7zM36 20h5v20h-5zM2 40h44v7H2zM20 24h8v6h-8z' }],
    operations: [
      { d: 'M17 2h14v5H17z' },
      { d: 'M10 8h28v39H10zM16 17h16v3.5H16zM16 25h16v3.5H16zM16 33h10v3.5H16z', cut: true }
    ],
    'op-other': [
      {
        d: 'M8 19a5 5 0 1 1 0 10 5 5 0 0 1 0-10zM24 19a5 5 0 1 1 0 10 5 5 0 0 1 0-10zM40 19a5 5 0 1 1 0 10 5 5 0 0 1 0-10z'
      }
    ],
    swan: [
      {
        d: 'M6 31c0-5 5-8 13-8h12c-1.6-4.6-3.5-8.4-3.5-12.5C27.5 5.8 31 3 35 3c3.2 0 5.6 1.8 6.8 4.6L38 9c-.8-1-1.8-1.4-3-1.1-2.6.8-1.6 5.6.2 11.4C38 28.8 33 36 22 36H13c-4.6 0-7-1.8-7-5z'
      },
      { d: 'M3 40h42v4H3z' }
    ],
    cow: [
      { d: 'M6 15h28v16H6zM34 11h9v13h-9zM35 6l3 5h-4zM42 6l1 5h-3z' },
      { d: 'M8 31h4.5v13H8zM15 31h4.5v13H15zM24 31h4.5v13H24zM30 31h4v13h-4zM4 15l2 0-1 12H3z' }
    ],
    balloon: [
      {
        d: 'M24 2c8 0 13.5 6 13.5 14.5C37.5 26 30.5 33 24 35c-6.5-2-13.5-9-13.5-18.5C10.5 8 16 2 24 2zM21.5 35h5L24 39z'
      },
      { d: 'M24 39c-4 3 4 5 0 8', line: true }
    ],
    trampoline: [
      { d: 'M3 19c0-3.5 9.4-6 21-6s21 2.5 21 6-9.4 6-21 6S3 22.5 3 19z' },
      { d: 'M6 21h3.5L7.5 44H4zM38.5 21H42l2 23h-3.5zM17 24.5h3.5V44H17zM27.5 24.5H31V44h-3.5z' }
    ],
    bird: [
      {
        d: 'M3 22c7-3 13-1 17 5 2-9 9-15 19-15l6-4-2 7c-2 9-9 16-21 17-8 .5-15-4-19-10z'
      }
    ],
    tree: [
      {
        d: 'M24 2a9.5 9.5 0 0 1 9 6.6 8.5 8.5 0 0 1 3.4 16.2A8 8 0 0 1 29 31H19a8 8 0 0 1-7.4-6.2A8.5 8.5 0 0 1 15 8.6 9.5 9.5 0 0 1 24 2z'
      },
      { d: 'M21.5 26h5v21h-5zM24 33l-6-5 2-2 4 3.5zM24 30l5-5 2 2-6 5z' }
    ],
    kite: [{ d: 'M30 2 44 18 27 32 14 16z' }, { d: 'M27 32c-3 4-8 3-10 7s-6 6-12 5', line: true }],
    sheep: [
      {
        d: 'M13 17a6.5 6.5 0 0 1 11-3 7 7 0 0 1 12 4 6 6 0 0 1-1 11.5 6.5 6.5 0 0 1-11 2 6.5 6.5 0 0 1-11-1A6 6 0 0 1 13 17zM38 15a5.5 5.5 0 1 1 0 11 5.5 5.5 0 0 1 0-11z'
      },
      { d: 'M14 31h3.5v12H14zM21 32h3.5v11H21zM28 32h3.5v11H28zM34 30h3.5v13H34z' }
    ],
    next: [{ d: 'M4 19h24V8l17 16-17 16V29H4z' }]
  };

  export const hasPictogram = (name: string) => name in shapes;
</script>

<script lang="ts">
  let { name }: { name: string } = $props();

  const parts = $derived(shapes[name] ?? shapes['op-other']);
</script>

<svg viewBox="0 0 48 48" aria-hidden="true" focusable="false">
  {#each parts as part, i (i)}
    {#if part.line}
      <path
        d={part.d}
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
      />
    {:else}
      <path d={part.d} fill="currentColor" fill-rule={part.cut ? 'evenodd' : undefined} />
    {/if}
  {/each}
</svg>

<style>
  svg {
    display: block;
    width: 100%;
    height: 100%;
  }
</style>
