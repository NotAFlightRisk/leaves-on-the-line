<script lang="ts">
  import '../app.css';
  import Masthead from '#lib/components/Masthead.svelte';

  let { children } = $props();

  const OGL = 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/';
</script>

<svg class="defs" aria-hidden="true">
  <defs>
    <pattern
      id="hatch"
      width="4"
      height="4"
      patternUnits="userSpaceOnUse"
      patternTransform="rotate(45)"
    >
      <rect width="1.5" height="4" fill="var(--hatch)" />
    </pattern>
  </defs>
</svg>
<a class="skip" href="#main">Skip to the numbers</a>
<Masthead />
<main id="main">
  {@render children()}
</main>
<footer>
  <p>
    Delay data from Network Rail's Historic Delay Attribution and ORR's Table 3184, station
    locations from NaPTAN. All of it's under the
    <a href={OGL}>Open Government Licence</a>, and this site isn't Network Rail or ORR or endorsed
    by either.
  </p>
  <p>
    <a href="/method">How it's worked out</a> ·
    <a href="https://github.com/NotAFlightRisk/leaves-on-the-line">Source on GitHub</a>
  </p>
</footer>

<style>
  .defs {
    position: absolute;
    width: 0;
    height: 0;
  }

  .skip {
    position: absolute;
    left: var(--space-4);
    top: -10rem;
    padding: var(--space-2) var(--space-3);
    background: var(--panel-raised);
    z-index: 10;

    &:focus {
      top: var(--space-2);
    }
  }

  main {
    max-width: var(--page);
    margin: 0 auto;
    padding: var(--space-6) var(--gutter) var(--space-8);
  }

  footer {
    max-width: var(--page);
    margin: 0 auto;
    padding: var(--space-6) var(--gutter) var(--space-7);
    border-top: 1px solid var(--rule);
    color: var(--text-muted);
    font-size: var(--step--1);
    display: grid;
    gap: var(--space-3);

    p {
      max-width: var(--measure);
    }
  }
</style>
