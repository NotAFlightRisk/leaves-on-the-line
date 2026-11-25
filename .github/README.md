<h1 align="center">Leaves on the Line</h1>
<p align="center">
<i>Why Britain's trains were late, cause by cause, for every station, route and operator</i>
<br />
<b>🌐 <a href="https://leaves.peng.ly/">leaves.peng.ly</a></b><br />
</p>

<details>
  <summary>Contents</summary>

- [About](#about)
- [The numbers](#the-numbers)
- [How the data gets here](#how-the-data-gets-here)
- [Deployment](#deployment)
- [Development](#development)
- [Credits](#credits)

</details>

## About

Network Rail puts a cause on every minute of delay, from signal failures to swans on the line, and publishes the lot as open data. Hardly anyone outside the industry reads it. This turns it into a page for every station, route and operator, a map of where each cause starts, trends since April 2018, and the odd ones (cows, trampolines, sunlight on signals).

It's built for people who need a number they can cite, like journalists, campaigners and councillors, and for commuters who've had a bad week and want to know if it was leaves, signals or the operator. It won't tell you why your train was late today, as the data lands six to ten weeks after each four-week period ends.

---

## The numbers

The short version, and the [method page](https://leaves.peng.ly/method) has the long one:

- A delay minute is a delay event on one of the 24 passenger operators' trains, which is how ORR counts them. Cancelled trains are counted as trains, never as minutes
- Station pages count delay picked up at the station or on the run to the next timing point. The map uses where each incident was instead
- Incidents involving people (fatalities, trespass, welfare, police searches, ill passengers) are taken out by incident before anything's summed, and only show as one network total a period
- Every figure carries the share of its minutes that Network Rail and the operators had agreed on, and periods whose file was under 94% agreed are hatched. Nothing's called final
- Each new file is checked against ORR's Table 3184 before it goes up

Every page has its numbers beside it as CSV and JSON, so `/station/pad` has `/station/pad.csv` and `/station/pad.json`, each row naming the Network Rail file it came from. The period rollups behind the whole site are in [`data/periods`](../data/periods), two gzipped CSVs and a `meta.json` a period.

All of it's from Network Rail, ORR and NaPTAN under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). If you use the figures, credit Network Rail's Historic Delay Attribution data, and this site if you like. We're not Network Rail or ORR, and neither has endorsed it.

---

## How the data gets here

The pipeline's Python, in [`pipeline/`](../pipeline). It reads each period's file, drops what isn't passenger delay, rolls the rest up by where it was recorded and where the incident was, and checks it against ORR.

```bash
uv run --project pipeline leaves backfill   # the 74 periods on Network Rail's old public bucket
uv run --project pipeline leaves update     # new or re-released periods from the marketplace drop
uv run --project pipeline leaves orr        # ORR's Table 3184
uv run --project pipeline leaves naptan     # station locations
uv run --project pipeline leaves site       # the JSON and CSVs the site's built from
```

Periods from 2023-24 P10 onwards only come through the [Rail Data Marketplace](https://raildata.org.uk/), which drops new files into an Azure Blob container. `update` reads that container from a SAS URL in `LEAVES_DROP`, and does nothing without one. The 🚂 Data workflow runs it daily, along with ORR's table, and NaPTAN monthly, then commits whatever changed.

A file with a reason code the glossary doesn't know, or a missing column, fails the run loudly rather than landing in "other". Add the code to [`data/glossary/reasons.csv`](../data/glossary/reasons.csv) and run it again. A period that fails the ORR check stays out until someone's looked at why; `update --accept` lets it in.

---

## Deployment

### Option 1: Cloudflare

It's entirely static, so it runs as Workers static assets with no Worker code. Change the route in `wrangler.jsonc`, then:

```bash
npm run data && npm run build
npx wrangler deploy
```

Ours deploys through the 🚀 Deploy workflow on every push to `main`.

### Option 2: Docker

There's a multi-arch image on DockerHub ([`notaflightrisk/leaves-on-the-line`](https://hub.docker.com/r/notaflightrisk/leaves-on-the-line)) and GHCR ([`ghcr.io/notaflightrisk/leaves-on-the-line`](https://github.com/NotAFlightRisk/leaves-on-the-line/pkgs/container/leaves-on-the-line)):

```bash
docker run -p 8080:8080 notaflightrisk/leaves-on-the-line
```

### Option 3: From a release

Each [release](https://github.com/NotAFlightRisk/leaves-on-the-line/releases) has the built site as `site.zip`, which works on any static host, plus every page's CSV in `figures.zip`.

### Option 4: Build from source

Follow [Development](#development), then `npm run build`, and `build/` is the whole site.

---

## Development

You'll need [Node](https://nodejs.org/) 22+, [uv](https://docs.astral.sh/uv/) and [Git](https://git-scm.com/).

```bash
git clone git@github.com:NotAFlightRisk/leaves-on-the-line.git
cd leaves-on-the-line
npm install
npm run data
npm run dev
```

`npm run data` builds the site's JSON from the rollups already in the repo, so there's no need to download anything. The dev server's then on [localhost:5173](http://localhost:5173).

Tests are `npm test` and `uv run --project pipeline pytest`, types are `npm run check`, and lint is `uv run --project pipeline ruff check`. Or build the container with `docker build -t leaves-on-the-line .`

---

## Credits

##### Contributors

[![contributors badge](https://readme-contribs.as93.net/contributors/NotAFlightRisk/leaves-on-the-line?shape=squircle)](https://github.com/NotAFlightRisk/leaves-on-the-line/graphs/contributors)

Delay data from Network Rail's Historic Delay Attribution, operator totals from ORR's Table 3184 and station locations from NaPTAN, all under the Open Government Licence v3.0. Map tiles from [OpenFreeMap](https://openfreemap.org), map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors.

---

<!-- License + Copyright -->
<p  align="center">
  <a href="https://github.com/NotAFlightRisk"><img width="64" src="https://pixelflare.cc/iain/gif/penguin-dance.gif" /></a><br>
  <sup>
    <i>Licensed under <a href="../LICENSE">MIT</a>, © <a href="https://peng.ly">NotAFlightRisk</a> 2026</i>
  </sup>
</p>

<!--
oooh, hello there! hope you're having a nice day :)
   |\__      |\___
 (:> __)X  (:o ___(
   |/        |/
-->
