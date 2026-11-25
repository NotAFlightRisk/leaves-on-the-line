<script lang="ts">
  import { goto } from '$app/navigation';

  type Station = [crs: string, name: string, minutes: number];

  let {
    id = 'station-search',
    large = false,
    label = 'Find a station'
  }: { id?: string; large?: boolean; label?: string } = $props();

  const SHOWN = 7;

  let stations: Station[] = $state([]);
  let query = $state('');
  let open = $state(false);
  let active = $state(-1);
  let missed = $state(false);

  const wanted = $derived(query.trim().toLowerCase());
  // the code first, then names that start with it, then any word that does, then anywhere
  const tests: ((crs: string, name: string) => boolean)[] = [
    (crs) => crs === wanted,
    (_, name) => name.startsWith(wanted),
    (_, name) => name.split(/[\s(-]+/).some((word) => word.startsWith(wanted)),
    (_, name) => name.includes(wanted)
  ];
  const matches = $derived.by(() => {
    if (!wanted) return [];
    // a station's rank is the first test it passes, and ties go to the busier one
    return stations
      .map((s) => ({ s, rank: tests.findIndex((test) => test(s[0], s[1].toLowerCase())) }))
      .filter((m) => m.rank >= 0)
      .sort((a, b) => a.rank - b.rank || b.s[2] - a.s[2])
      .slice(0, SHOWN)
      .map(({ s: [crs, name] }) => {
        const at = name.toLowerCase().indexOf(wanted);
        return {
          crs,
          name,
          parts:
            at < 0
              ? [name, '', '']
              : [
                  name.slice(0, at),
                  name.slice(at, at + wanted.length),
                  name.slice(at + wanted.length)
                ]
        };
      });
  });
  const expanded = $derived(open && matches.length > 0);

  // fetched once, the first time anyone reaches for the search
  let loading: Promise<void> | undefined;
  function prime() {
    loading ??= fetch('/data/stations.json')
      .then((response) => {
        if (!response.ok) throw new Error(`stations.json answered ${response.status}`);
        return response.json();
      })
      .then((list: Station[]) => {
        stations = list;
      })
      .catch((problem) => {
        // let the next focus try again
        loading = undefined;
        console.error(problem);
      });
    return loading;
  }

  function choose(crs: string) {
    query = '';
    open = false;
    active = -1;
    missed = false;
    goto(`/station/${crs}`);
  }

  async function go(event: SubmitEvent) {
    event.preventDefault();
    await prime();
    const hit = matches[Math.max(active, 0)];
    missed = !hit;
    if (hit) choose(hit.crs);
  }

  function keys(event: KeyboardEvent) {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      open = true;
      if (!matches.length) return;
      // -1 is the input itself, so the arrows wrap round through it
      const step = event.key === 'ArrowDown' ? 1 : -1;
      const slots = matches.length + 1;
      active = ((active + 1 + step + slots) % slots) - 1;
    } else if (event.key === 'Escape') {
      if (expanded) open = false;
      else query = '';
      active = -1;
    }
  }
</script>

<form role="search" class:large onsubmit={go}>
  <label class={large ? 'label' : 'visually-hidden'} for={id}>{label}</label>
  <div class="combo">
    <div class="field">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" />
      </svg>
      <input
        {id}
        type="search"
        role="combobox"
        placeholder={large ? 'Like Leeds or LDS' : 'Find a station'}
        autocomplete="off"
        spellcheck="false"
        aria-autocomplete="list"
        aria-expanded={expanded}
        aria-controls="{id}-list"
        aria-activedescendant={expanded && active >= 0 ? `${id}-option-${active}` : undefined}
        aria-invalid={missed || undefined}
        aria-describedby={missed ? `${id}-miss` : undefined}
        bind:value={query}
        onfocus={() => {
          prime();
          open = true;
        }}
        onblur={() => (open = false)}
        oninput={() => {
          missed = false;
          open = true;
          active = -1;
        }}
        onkeydown={keys}
      />
      <button type="submit">Go</button>
    </div>
    <ul id="{id}-list" role="listbox" aria-label="Stations" class="list" hidden={!expanded}>
      {#each matches as m, i (m.crs)}
        <!-- keys move through these from the input, as a combobox does, so a click is the pointer's way in -->
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <li
          id="{id}-option-{i}"
          role="option"
          aria-selected={i === active}
          class:active={i === active}
          onmousedown={(event) => event.preventDefault()}
          onclick={() => choose(m.crs)}
          onmousemove={() => (active = i)}
        >
          <span class="name">{m.parts[0]}<strong>{m.parts[1]}</strong>{m.parts[2]}</span>
          <span class="crs">{m.crs.toUpperCase()}</span>
        </li>
      {/each}
    </ul>
  </div>
  {#if missed}
    <p id="{id}-miss" class="miss" role="status">
      No station by that name. Try its code, like PAD.
    </p>
  {/if}
</form>

<style>
  form {
    position: relative;
    display: grid;
    gap: var(--space-2);
  }

  .label {
    font-weight: 800;
    font-size: var(--step-1);
  }

  .combo {
    position: relative;
  }

  .field {
    display: flex;
    align-items: center;
    background: var(--panel);
    color: var(--text);
    border-radius: var(--radius);
    padding-left: var(--space-3);

    &:focus-within {
      outline: 3px solid var(--edge);
      outline-offset: 2px;
    }

    svg {
      flex: none;
      width: 1.2rem;
      height: 1.2rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.4;
      stroke-linecap: round;
    }

    input:focus-visible,
    button:focus-visible {
      outline: none;
      box-shadow: none;
    }

    button:focus-visible {
      box-shadow: inset 0 0 0 3px var(--sign);
    }
  }

  input {
    width: min(15rem, 52vw);
    min-height: 2.75rem;
    padding: var(--space-2) var(--space-3);
    background: transparent;
    border: 0;

    &::placeholder {
      color: var(--text-faint);
    }

    &::-webkit-search-cancel-button {
      display: none;
    }
  }

  .field:has([aria-invalid]) {
    box-shadow: inset 0 0 0 2px var(--cause-assets);
  }

  button {
    align-self: stretch;
    min-width: 3.25rem;
    padding: 0 var(--space-4);
    background: var(--edge);
    color: var(--sign);
    font-weight: 800;
    border: 0;
    border-radius: 0 var(--radius) var(--radius) 0;
    cursor: pointer;

    &:hover {
      background: #ffd83d;
    }
  }

  .list {
    position: absolute;
    left: 0;
    right: 0;
    top: calc(100% + var(--space-2));
    z-index: 30;
    margin: 0;
    padding: var(--space-1) 0;
    list-style: none;
    background: var(--panel);
    color: var(--text);
    border-radius: var(--radius);
    box-shadow:
      0 0 0 2px var(--sign),
      0 16px 32px -12px rgb(16 38 74 / 0.45);
    overflow: hidden;

    &[hidden] {
      display: none;
    }
  }

  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
    min-height: 2.75rem;
    padding: var(--space-2) var(--space-3);
    cursor: pointer;

    strong {
      font-weight: 800;
      text-decoration: underline;
      text-decoration-color: var(--edge);
      text-decoration-thickness: 3px;
      text-underline-offset: 0.15em;
    }

    &.active {
      background: var(--sign);
      color: var(--on-sign);

      .crs {
        background: var(--edge);
        color: var(--sign);
      }
    }
  }

  .name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .crs {
    flex: none;
    padding: 0.05rem var(--space-2);
    border-radius: var(--radius-chip);
    background: var(--panel-raised);
    font-size: 0.8125rem;
    font-weight: 800;
    letter-spacing: 0.05em;
  }

  .large {
    .field {
      box-shadow: inset 0 0 0 2px var(--sign);
      padding-left: var(--space-4);
    }

    input {
      width: 100%;
      min-height: 3.5rem;
      font-size: var(--step-1);
    }

    button {
      min-width: 5rem;
      font-size: var(--step-1);
      box-shadow: inset 0 0 0 2px var(--sign);
    }

    li {
      font-size: var(--step-0);
    }

    .field:focus-within {
      outline-color: var(--sign);
    }
  }

  .miss {
    position: absolute;
    top: calc(100% + var(--space-1));
    right: 0;
    width: max-content;
    max-width: 80vw;
    padding: var(--space-2) var(--space-3);
    background: var(--edge);
    color: var(--sign);
    font-weight: 600;
    border-radius: var(--radius);
    font-size: var(--step--1);
    z-index: 5;
  }
</style>
