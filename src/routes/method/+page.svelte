<script lang="ts">
  import { cause, covers } from '#lib/causes.ts';
  import { dateLong, dateMonth } from '#lib/format.ts';
  import Meta from '#lib/components/Meta.svelte';

  let { data } = $props();

  const related = [
    {
      slug: 'tubespotting',
      name: 'Tube Spotting',
      about: 'a live map of every Tube train in London',
      url: 'https://tubespotting.peng.ly'
    },
    {
      slug: 'floodpulse',
      name: 'floodpulse',
      about: 'river levels and flood warnings across England',
      url: 'https://floodpulse.peng.ly'
    },
    {
      slug: 'carbonara',
      name: 'carbonara',
      about: "how clean Britain's electricity is right now",
      url: 'https://carbonara.peng.ly'
    },
    {
      slug: 'track-the-gap',
      name: 'Track the Gap',
      about: "how the Tube's really running, line by line",
      url: 'https://track-the-gap.peng.ly'
    },
    {
      slug: 'enshittification',
      name: 'The Enshittification Index',
      about: 'big tech making things worse, dated and sourced',
      url: 'https://enshittification.peng.ly'
    }
  ];

  const index = $derived(data.index);
  const first = $derived(index.periods[0]);
  const last = $derived(index.periods[index.last]);
  const sources = $derived([
    {
      title: 'Historic Delay Attribution',
      provider: 'Network Rail',
      url: 'https://raildata.org.uk/dashboard/dataProduct/P-b5f4216b-4de5-412f-9c9a-d14c604a6b9e/overview',
      what: `Every delay and cancellation with its cause, from ${dateMonth(first.start)} to ${dateMonth(last.end)}. Older files come from Network Rail's public downloads, and newer ones from the Rail Data Marketplace.`,
      taken: index.taken['network-rail']
    },
    {
      title: 'Table 3184: delay minutes by operator and cause, periodic',
      provider: 'Office of Rail and Road',
      url: 'https://dataportal.orr.gov.uk/statistics/performance/passenger-rail-performance/table-3184-delay-minutes-by-operator-and-cause-periodic/',
      what: "Used to check our totals, and for the months after Network Rail's files end.",
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
    Every number here comes from Network Rail's delay records or ORR's published tables, added up
    and nothing more. This page sets out exactly what's counted, so you can check it, quote it or
    pick holes in it.
  </p>

  <section>
    <h2>What a delay minute is</h2>
    <p>
      Network Rail logs every time a train loses time against its timetable, and gives it a cause.
      We count these delay reports for the 24 passenger operators in ORR's tables, the same way ORR
      does. Freight, charter, Eurostar and London Underground trains are in the files too, but we
      leave them out.
    </p>
    <p>
      The files also give cancelled trains a number of minutes. Those minutes are estimated, not
      lost, and Network Rail's own guide warns against counting them as delay. So we count
      cancellations as trains. Each train cancelled in full or in part counts once, under the
      incident that caused it. A cancellation with no incident against it isn't counted, because it
      has no cause.
    </p>
  </section>

  <section>
    <h2>Where the delay is recorded</h2>
    <p>
      Station pages show where trains lost the time. Network Rail calls this the location of the
      delay, as opposed to the location of the incident. It's either a station or the stretch of
      line from it to the next timing point. About half is at the station itself, and a fifth is on
      stretches of 10 km or more. Delay recorded somewhere that isn't a station, like a junction or
      a signal, stays off station pages. It still counts on route and operator pages.
    </p>
    <p>
      The map shows where each incident happened instead. So a failed signal shows where it failed,
      even though the trains it held up were late all over the place.
    </p>
  </section>

  <section>
    <h2>Knock-on delay</h2>
    <p>
      About two thirds of all delay is knock-on, which Network Rail calls reactionary. That's a
      train held up because another train was late first. It's put down to the incident that started
      it, so a signal failure at Reading can explain minutes lost at Paddington. Each page says how
      much of its delay was knock-on.
    </p>
  </section>

  <section>
    <h2>The causes</h2>
    <p>
      We use ORR's cause groups, and every reason code in Network Rail's glossary belongs to one of
      them. We split autumn out from weather. Network Rail's causes come first, then the operators'.
      A cause belongs to whoever the delay was put down to, not to the kind of thing that went
      wrong.
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
    <h2>Months</h2>
    <p>
      Network Rail splits its year into 13 periods, starting on 1 April. Most are four weeks long,
      but they run from 25 to 32 days. The rest of this site calls them months to keep things
      simple. It compares them per day, so a long one doesn't look worse than a short one.
    </p>
  </section>

  <section>
    <h2 id="recent">Recent months</h2>
    <p>
      Network Rail's detailed files on this site stop at {dateLong(last.end)}. Newer ones are only
      on the Rail Data Marketplace. For later months, the homepage and trends page use ORR's Table
      3184 instead.
    </p>
    <p>
      ORR counts a few things differently. It includes delay involving people, it can't split autumn
      from weather, and it leaves out lines that aren't Network Rail's. So the two sources are never
      added together, and a month is only compared with months from the same source. ORR doesn't
      break delay down by station, so station pages stop at {dateMonth(last.end)}.
    </p>
  </section>

  <section>
    <h2>Comparing with other years</h2>
    <p>
      Each cause is compared with the same month in other years, per day, because months run from 25
      to 32 days. We leave out 2020-21, when lockdown timetables ran. The result shows where this
      year sits among the others. It's never shown as "X% worse than normal", because more trains
      mean more minutes, and the files can't say how many trains ran. A station with under 100
      minutes of delay a month on average gets its numbers, but no comparison.
    </p>
  </section>

  <section>
    <h2>Still being agreed</h2>
    <p>
      Network Rail and the operators can disagree about who caused a delay. When a month's figures
      first come out, a lot can still be open. Every file says how much of its delay was agreed.
      Charts go by the whole file, so a month under 94% agreed is striped. The agreed share beside a
      figure covers only the minutes in that figure. That's how a station can be 99% agreed inside a
      striped month. Nothing is called final, and a re-released month replaces the old one.
    </p>
  </section>

  <section>
    <h2>What's left out, and why</h2>
    <p>
      Incidents involving people are left out. These are fatalities, trespass, welfare concerns and
      disorder, police searches of the line or a train, and ill or injured passengers. Trespass is
      also where Network Rail records people in crisis on the line. Together they make up between a
      tenth and an eighth of delay. We take them out incident by incident before adding anything up,
      knock-on delay included. They appear only as one network total a month on the trends page.
      Nothing below the whole network is shown by day either, so no figure can point to a day and a
      place. This follows Samaritans' media guidance.
    </p>
    <p>
      The map can only draw a stretch of line with a station at one or both ends. Delay that starts
      at junctions and sidings with no station at either end isn't on it. That's 14% of delay since
      2018. It's still in every route and operator total, and the map says how much it's leaving out
      for whatever you've picked.
    </p>
  </section>

  <section>
    <h2>Routes and operators</h2>
    <p>
      Routes are today's Network Rail routes, applied to every year. Operators keep their codes when
      a franchise changes hands. So Avanti West Coast's page includes Virgin's years on the West
      Coast, and each operator page names who ran it before.
    </p>
  </section>

  <section>
    <h2>Checking it against ORR</h2>
    <p>
      Each new file is checked against ORR's Table 3184 before it goes up. For operators that only
      run on Network Rail's track, our totals have to land within 2% of ORR's. In a month at least
      94% agreed, nine in ten of their causes over 500 minutes also have to land within 10%. The
      Elizabeth line, Heathrow Express, Chiltern, Transport for Wales, London Overground and
      Southeastern run partly off Network Rail's track. ORR leaves that part out and the files
      don't, so their totals come out higher and aren't held to the check. A file that fails stays
      out until someone has looked at why.
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
      This site isn't run or endorsed by Network Rail or ORR. Every page has its numbers as a CSV
      file, and the monthly totals behind them are in the
      <a href="https://github.com/NotAFlightRisk/leaves-on-the-line">repo</a>.
    </p>
  </section>

  <section>
    <h2>More from us</h2>
    <ul class="related">
      {#each related as app (app.slug)}
        <li>
          <img
            src="https://portfolio.peng.ly/logos/{app.slug}.svg"
            alt=""
            width="20"
            height="20"
            loading="lazy"
          />
          <span><a href={app.url}>{app.name}</a> - {app.about}</span>
        </li>
      {/each}
    </ul>
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
    border-radius: var(--radius-chip);
  }

  .sources {
    margin: 0;
    padding-left: var(--space-5);
    display: grid;
    gap: var(--space-3);
  }

  .related {
    margin: 0;
    padding: 0;
    display: grid;
    gap: var(--space-2);
    list-style: none;

    li {
      display: flex;
      gap: var(--space-2);
    }

    img {
      flex: none;
      height: 1lh;
    }
  }
</style>
