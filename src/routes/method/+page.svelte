<script lang="ts">
  import { cause, covers } from '#lib/causes.ts';
  import { dateLong } from '#lib/format.ts';
  import Meta from '#lib/components/Meta.svelte';

  let { data } = $props();

  const index = $derived(data.index);
  const first = $derived(index.periods[0]);
  const last = $derived(index.periods[index.last]);
  const sources = $derived([
    {
      title: 'Historic Delay Attribution',
      provider: 'Network Rail',
      url: 'https://raildata.org.uk/dashboard/dataProduct/P-b5f4216b-4de5-412f-9c9a-d14c604a6b9e/overview',
      what: `Every delay and cancellation with its cause, ${first.label} to ${last.label}. The older files come from Network Rail's own public download area, newer ones from the Rail Data Marketplace.`,
      taken: index.taken['network-rail']
    },
    {
      title: 'Table 3184: delay minutes by operator and cause, periodic',
      provider: 'Office of Rail and Road',
      url: 'https://dataportal.orr.gov.uk/statistics/performance/passenger-rail-performance/table-3184-delay-minutes-by-operator-and-cause-periodic/',
      what: 'Used to check our totals, and drawn on its own in the trends for periods we have no file for.',
      taken: index.taken.orr
    },
    {
      title: 'NaPTAN, national rail stations',
      provider: 'Department for Transport',
      url: 'https://beta-naptan.dft.gov.uk/',
      what: 'Where each station is, matched to the glossary by its three-letter code.',
      taken: index.taken.naptan
    }
  ]);
</script>

<Meta
  title="How it's worked out"
  description="What a delay minute is on Leaves on the Line, where it's recorded, what's left out and why, and every source with its licence."
/>

<article class="method">
  <h1>How it's worked out</h1>
  <p class="lead">
    Every number here comes from Network Rail's own delay attribution files, summed up and nothing
    else. Here's exactly what's counted, so you can check it, quote it or pick holes in it.
  </p>

  <section>
    <h2>What a delay minute is</h2>
    <p>
      Network Rail logs every time a train loses time against its timetable and puts a cause on it.
      We count those delay events (automatic and manual delay reports) on the 24 passenger operators
      in ORR's tables, which is how ORR counts them. Freight, charters, Eurostar and the
      Underground's trains are in the files too and stay out.
    </p>
    <p>
      The files also give cancelled trains a number of minutes, but those are deemed, not lost, and
      Network Rail's own guide says counting them as delay is misleading. So cancellations are
      counted as trains: each train cancelled in full or in part is one train, under the incident
      that caused it. A cancellation nobody's put down to an incident isn't counted, since it has no
      cause.
    </p>
  </section>

  <section>
    <h2>Where the delay is recorded</h2>
    <p>
      Station pages use where the train lost the time, which Network Rail calls the location of the
      delay, not the incident. That's a station or the run from it to the next timing point: about
      half of it is at the station itself and a fifth is on runs of 10 km or more. Delay recorded
      somewhere that isn't a station (a junction or a signal) stays off station pages but counts on
      the route and operator pages.
    </p>
    <p>
      The map uses where each incident was instead, so a failed signal shows where it failed even
      though the trains it held up were late all over the place.
    </p>
  </section>

  <section>
    <h2>Knock-on delay</h2>
    <p>
      About two thirds of all delay is knock-on (Network Rail says reactionary): a train held up
      because another train was late first. It's put down to the incident that started it, so a
      signal failure at Reading can explain minutes lost at Paddington. Each page says how much of
      its delay was knock-on.
    </p>
  </section>

  <section>
    <h2>The causes</h2>
    <p>
      ORR's own groups, which the glossary tags every reason code with, with autumn split out of
      weather. Network Rail's causes first, then the operators'. Whose cause it is comes from who
      the delay was attributed to, not what kind of thing went wrong.
    </p>
    <dl class="causes">
      {#each index.groups as group (group.id)}
        <div>
          <dt><span class="chip" style:background={cause(group.id)}></span>{group.label}</dt>
          <dd>{covers[group.id]}. ORR calls it {group.orr}.</dd>
        </div>
      {/each}
    </dl>
  </section>

  <section>
    <h2>Comparing with other years</h2>
    <p>
      Each cause is read against the same period in other years, per day since periods run from 25
      to 32 days, leaving out 2020-21 when lockdown timetables ran. It's shown as where this year
      sits among the others and never as "X% worse than normal": more trains mean more minutes, and
      the files can't say how many ran. A station averaging under 100 delay minutes a period gets
      its numbers but no comparison.
    </p>
  </section>

  <section>
    <h2>Still being agreed</h2>
    <p>
      Network Rail and the operators can dispute who caused a delay, and a period's first release
      can have a lot still open. Every file says how much of its delay was agreed. The charts go by
      the whole file, so a period whose file was under 94% agreed is hatched, while the share next
      to a figure is just the minutes in that figure, which is how a station can be 99% agreed
      inside a hatched period. Nothing's called final, and a re-release of a period replaces the old
      one.
    </p>
  </section>

  <section>
    <h2>What's left out, and why</h2>
    <p>
      Incidents involving people: fatalities, trespass (which is also where people in crisis on the
      line get coded), welfare concerns and disorder, police searching the line or a train, and ill
      or injured passengers. They're between a tenth and an eighth of delay. They're taken out by
      incident before anything is summed, knock-on and all, and appear only as one network total a
      period on the trends page. Nothing below the whole network is shown by day either, so no
      figure can point at a day and a place. This follows Samaritans' media guidance.
    </p>
    <p>
      The map can only draw a section of line with a station at one end or both, so the delay that
      starts at junctions and sidings with no station at either end (14% of it since 2018) isn't on
      it, though it's in every route and operator total. The map says how much it's leaving off for
      whatever you've picked.
    </p>
  </section>

  <section>
    <h2>Routes and operators</h2>
    <p>
      Routes are today's Network Rail routes from the glossary, applied to every year. Operators
      keep their codes when franchises change hands, so Avanti West Coast's page includes Virgin's
      West Coast years, and each operator page names who ran it before.
    </p>
  </section>

  <section>
    <h2>Checking it against ORR</h2>
    <p>
      Each new file is checked against ORR's Table 3184 before it goes up. For the operators that
      only run on Network Rail's track, our totals have to land within 2% of ORR's, and on a period
      at least 94% agreed, nine in ten of their causes over 500 minutes have to land within 10%. The
      Elizabeth line, Heathrow Express, Chiltern, Transport for Wales, London Overground and
      Southeastern run partly off Network Rail's track, which ORR leaves out and the files don't, so
      they come out higher and aren't held to it. A file that fails stays out until someone's looked
      at why.
    </p>
  </section>

  <section>
    <h2>Sources</h2>
    <ul class="sources">
      {#each sources as source (source.title)}
        <li>
          <a href={source.url}>{source.title}</a>, {source.provider}. {source.what} Open Government Licence
          v3.0. Last taken {dateLong(source.taken)}.
        </li>
      {/each}
      <li>
        Map tiles from <a href="https://openfreemap.org">OpenFreeMap</a>, map data ©
        <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.
      </li>
    </ul>
    <p>
      This site isn't Network Rail or ORR, and neither has endorsed it. Every page's numbers are a
      CSV beside it, and the period rollups behind them are in the
      <a href="https://github.com/NotAFlightRisk/leaves-on-the-line">repo</a>.
    </p>
  </section>
</article>

<style>
  .method {
    display: grid;
    gap: var(--space-6);
    max-width: var(--measure);

    h1 {
      font-size: var(--step-3);
    }
  }

  .lead {
    font-size: var(--step-1);
  }

  section {
    display: grid;
    gap: var(--space-3);

    h2 {
      font-size: var(--step-1);
      margin-top: var(--space-3);
    }
  }

  .causes {
    margin: 0;
    display: grid;
    gap: var(--space-3);

    dt {
      font-weight: 700;
    }

    dd {
      margin: 0 0 0 calc(0.75rem + var(--space-2));
      color: var(--text-muted);
    }
  }

  .chip {
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
    margin-right: var(--space-2);
    border-radius: 2px;
  }

  .sources {
    margin: 0;
    padding-left: var(--space-5);
    display: grid;
    gap: var(--space-3);
  }
</style>
