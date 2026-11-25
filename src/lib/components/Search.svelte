<script lang="ts">
  import { goto } from '$app/navigation';

  type Station = [crs: string, name: string, minutes: number];

  let stations: Station[] = $state([]);
  let query = $state('');
  let missed = $state(false);

  async function prime() {
    if (stations.length) return;
    stations = await (await fetch('/data/stations.json')).json();
  }

  function find(text: string) {
    const wanted = text.trim().toLowerCase();
    return stations.find(
      ([crs, name]) => name.toLowerCase() === wanted || crs.toLowerCase() === wanted
    );
  }

  async function go(event: SubmitEvent) {
    event.preventDefault();
    await prime();
    const hit =
      find(query) ??
      stations.find(([, name]) => name.toLowerCase().startsWith(query.trim().toLowerCase()));
    missed = !hit;
    if (hit) {
      query = '';
      goto(`/station/${hit[0]}`);
    }
  }
</script>

<form role="search" onsubmit={go}>
  <label class="visually-hidden" for="station-search">Find a station</label>
  <input
    id="station-search"
    type="search"
    list="station-names"
    placeholder="Find a station"
    autocomplete="off"
    bind:value={query}
    onfocus={prime}
    oninput={() => (missed = false)}
    aria-invalid={missed || undefined}
    aria-describedby={missed ? 'search-miss' : undefined}
  />
  <datalist id="station-names">
    {#each stations as [crs, name] (crs)}
      <option value={name}>{crs}</option>
    {/each}
  </datalist>
  <button type="submit">Go</button>
  {#if missed}
    <p id="search-miss" class="miss" role="status">
      No station by that name. Try its code, like PAD.
    </p>
  {/if}
</form>

<style>
  form {
    position: relative;
    display: flex;
    gap: var(--space-2);
  }

  input {
    width: min(16rem, 60vw);
    padding: var(--space-2) var(--space-3);
    background: var(--panel);
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius);

    &::placeholder {
      color: var(--text-faint);
    }

    &[aria-invalid] {
      border-color: var(--cause-external);
    }
  }

  button {
    padding: var(--space-2) var(--space-4);
    background: var(--panel-raised);
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius);
    cursor: pointer;

    &:hover {
      border-color: var(--figure);
    }
  }

  .miss {
    position: absolute;
    top: calc(100% + var(--space-1));
    right: 0;
    width: max-content;
    max-width: 80vw;
    padding: var(--space-2) var(--space-3);
    background: var(--panel-raised);
    border: 1px solid var(--rule-strong);
    font-size: var(--step--1);
    z-index: 5;
  }
</style>
