<script lang="ts">
  import { page } from '$app/state';
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
  <a class="wordmark" href="/">
    <span class="lamp" aria-hidden="true"></span>
    Leaves on the Line
  </a>
  <nav aria-label="Main">
    {#each links as [href, label] (href)}
      <a {href} aria-current={page.url.pathname.startsWith(href) ? 'page' : undefined}>{label}</a>
    {/each}
  </nav>
  <Search />
</header>

<style>
  header {
    max-width: var(--page);
    margin: 0 auto;
    padding: var(--space-4) var(--gutter);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3) var(--space-6);
    border-bottom: 1px solid var(--rule);
  }

  .wordmark {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    color: var(--text);
    font-weight: 700;
    font-size: var(--step-1);
    text-decoration: none;
    letter-spacing: -0.01em;
  }

  .lamp {
    width: 0.6em;
    height: 0.6em;
    border-radius: 50%;
    background: var(--figure);
    box-shadow: 0 0 0.5em var(--figure-glow);
  }

  nav {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1) var(--space-4);
    margin-right: auto;

    a {
      color: var(--text-muted);
      text-decoration: none;
      padding-block: var(--space-1);
      border-bottom: 2px solid transparent;

      &:hover {
        color: var(--text);
      }

      &[aria-current='page'] {
        color: var(--text);
        border-bottom-color: var(--figure);
      }
    }
  }
</style>
