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
  <div class="inner">
    <p>
      The figures come from Network Rail, the Office of Rail and Road (ORR) and the Department for
      Transport, under the <a href={OGL}>Open Government Licence</a>. This site isn't run or
      endorsed by Network Rail or ORR.
    </p>
    <p class="links">
      <a href="/method">How it's worked out</a>
      <a href="https://github.com/NotAFlightRisk/leaves-on-the-line">Source on GitHub</a>
    </p>
  </div>
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
    background: var(--edge);
    color: var(--sign);
    font-weight: 800;
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
    background: var(--sign);
    color: var(--on-sign-muted);
    border-top: 10px solid var(--edge);
    font-size: var(--step--1);

    a {
      color: var(--on-sign);
    }
  }

  .inner {
    max-width: var(--page);
    margin: 0 auto;
    padding: var(--space-6) var(--gutter) var(--space-7);
    display: grid;
    gap: var(--space-3);

    p {
      max-width: var(--measure);
    }
  }

  .links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2) var(--space-5);
  }
</style>
