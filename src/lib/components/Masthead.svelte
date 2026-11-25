<script lang="ts">
  import { page } from '$app/state';
  import Pictogram from './Pictogram.svelte';
  import Search from './Search.svelte';

  const links = [
    ['/stations', 'Stations'],
    ['/map', 'Map'],
    ['/trends', 'Trends'],
    ['/odd', 'Odd ones'],
    ['/method', 'Method']
  ];
</script>

<header>
  <div class="bar">
    <a class="wordmark" href="/">
      <span class="tile"><Pictogram name="autumn" /></span>
      Leaves on the Line
    </a>
    <nav aria-label="Main">
      {#each links as [href, label] (href)}
        <a {href} aria-current={page.url.pathname.startsWith(href) ? 'page' : undefined}>{label}</a>
      {/each}
    </nav>
    <Search />
  </div>
</header>

<style>
  header {
    background: var(--sign);
    color: var(--on-sign);
    border-bottom: 10px solid var(--edge);
  }

  .bar {
    max-width: var(--page);
    margin: 0 auto;
    padding: var(--space-3) var(--gutter);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3) var(--space-6);
  }

  .wordmark {
    display: inline-flex;
    align-items: center;
    gap: var(--space-3);
    color: var(--on-sign);
    font-weight: 800;
    font-size: var(--step-1);
    text-decoration: none;
    letter-spacing: -0.01em;
  }

  .tile {
    width: 2.5rem;
    height: 2.5rem;
    padding: 0.45rem;
    border-radius: var(--radius);
    background: var(--on-sign);
    color: var(--sign);
  }

  nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0 var(--space-5);
    margin-right: auto;

    a {
      color: var(--on-sign);
      font-weight: 600;
      text-decoration: none;
      padding-block: var(--space-2);
      border-bottom: 3px solid transparent;

      &:hover {
        border-bottom-color: var(--on-sign-muted);
      }

      &[aria-current='page'] {
        border-bottom-color: var(--edge);
      }
    }
  }

  @media (max-width: 30rem) {
    nav {
      gap: 0 var(--space-4);
      font-size: var(--step--1);
    }
  }
</style>
