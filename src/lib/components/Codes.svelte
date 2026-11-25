<script lang="ts">
  import type { Code } from '#lib/data.ts';
  import { minutes } from '#lib/format.ts';

  let { latest, all, period }: { latest: Code[]; all: Code[]; period: string } = $props();

  const lists = $derived([
    [`In ${period}`, latest],
    ['Since 2018', all]
  ] as const);
</script>

<div class="codes">
  {#each lists as [title, codes] (title)}
    <table>
      <caption>{title}</caption>
      <thead>
        <tr>
          <th scope="col">Code</th>
          <th scope="col">What Network Rail logged</th>
          <th scope="col" class="num">Minutes</th>
        </tr>
      </thead>
      <tbody>
        {#each codes as [code, description, value] (code)}
          <tr>
            <td class="code">{code}</td>
            <td>{description}</td>
            <td class="num">{minutes(value)}</td>
          </tr>
        {:else}
          <tr><td colspan="3" class="none">Nothing logged.</td></tr>
        {/each}
      </tbody>
    </table>
  {/each}
</div>

<style>
  .codes {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 26rem), 1fr));
    gap: var(--space-6);
  }

  table {
    width: 100%;
    font-size: var(--step--1);
  }

  caption {
    text-align: left;
    font-weight: 700;
    padding-bottom: var(--space-2);
  }

  th,
  td {
    padding: var(--space-2) var(--space-2);
    border-bottom: 1px solid var(--rule);
    text-align: left;
    vertical-align: top;
  }

  th {
    color: var(--text-faint);
    font-weight: 400;
  }

  .code {
    font-weight: 700;
    color: var(--text-muted);
  }

  .num {
    text-align: right;
    white-space: nowrap;
  }

  .none {
    color: var(--text-muted);
  }
</style>
