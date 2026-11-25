"""Turns the rollups into the JSON and CSVs the site prerenders from"""

import csv
import io
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from . import codes, naptan, orr, rollup
from .codes import GROUPS, PEOPLE
from .paths import DATA, PERIODS, STATIC

SITE = 'https://leaves.peng.ly'
GROUP_IDS = list(GROUPS)
ORR_GROUPS = [g for g in GROUP_IDS if g != 'autumn']
# a station averaging under this many delay minutes a period gets its numbers but no comparison
QUIET = 100
LICENCE = (
    'Contains Network Rail and ORR data under the Open Government Licence v3.0. '
    'Delay minutes are delay events on passenger trains, with incidents involving people left out.'
)


# the glossary's names for a few routes read like company filings
ROUTE_NAMES = {
    'The Chiltern Railway Co Ltd': 'Chiltern',
    'TfW Cardiff Valleys': 'Cardiff Valleys',
    'Private Railway': 'Private railways',
}


def route_name(raw: str) -> str:
    return ROUTE_NAMES.get(raw, raw)


def slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def title(text: str) -> str:
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda m: m[0].capitalize(), text.strip())


class Page:
    """One station, route, operator or the whole network, period by period"""

    def __init__(self, size: int):
        self.size = size
        self.minutes = defaultdict(lambda: [0.0] * size)
        self.cancelled = defaultdict(lambda: [0] * size)
        self.resp = defaultdict(lambda: [0.0] * size)
        self.unagreed = [0.0] * size
        self.knock = [0.0] * size
        self.codes = Counter()
        self.latest = Counter()

    def add(self, at: int, last: bool, group: str, row: dict, minutes: float) -> None:
        self.minutes[group][at] += minutes
        self.unagreed[at] += float(row['unagreed'])
        self.cancelled[group][at] += int(row['cancelled'])
        self.resp[row['responsible']][at] += minutes
        if row['kind'] == 'r':
            self.knock[at] += minutes
        self.codes[row['reason']] += minutes
        if last:
            self.latest[row['reason']] += minutes

    @property
    def total(self) -> list[float]:
        return [sum(self.minutes[g][at] for g in GROUP_IDS) for at in range(self.size)]

    def series(self, values: list, have: set[int]) -> list:
        return [round(v, 1) if i in have else None for i, v in enumerate(values)]

    def check(self, name: str) -> list[str]:
        out = []
        for at, total in enumerate(self.total):
            for part, values in (('knock-on', self.knock), ('unagreed', self.unagreed)):
                if values[at] > total + 0.5:
                    out.append(f'{name}: period {at} has more {part} minutes than minutes')
        return out

    def json(self, have: set[int], reasons: dict) -> dict:
        def top(counter):
            return [
                [c, reasons[c]['description'], round(m, 1)]
                for c, m in counter.most_common(10)
                if m > 0
            ]

        return {
            'minutes': {
                g: self.series(self.minutes[g], have) for g in GROUP_IDS if any(self.minutes[g])
            },
            'cancelled': {
                g: [v if i in have else None for i, v in enumerate(self.cancelled[g])]
                for g in GROUP_IDS
                if any(self.cancelled[g])
            },
            'unagreed': self.series(self.unagreed, have),
            'knock': self.series(self.knock, have),
            'codes': {'latest': top(self.latest), 'all': top(self.codes)},
        }


def axis(metas: dict[str, dict], table: dict) -> list[dict]:
    """Every period from the first file to the newest of our files and ORR's table"""
    calendar = codes.calendar()
    last = max([*metas, *table])
    out = []
    for period, row in calendar.items():
        if min(metas) <= period <= last:
            meta = metas.get(period)
            out.append(
                {
                    'id': period,
                    'label': period.replace('-P', ' P'),
                    'start': row['start'],
                    'end': row['end'],
                    'days': int(row['days']),
                    'file': meta and meta['source']['file'],
                    'released': meta and meta['source']['released'],
                    'agreed': meta and meta['file_agreed'],
                }
            )
    return out


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(',', ':')))


def write_csv(
    path: Path,
    url: str,
    page: Page,
    periods: list[dict],
    have: set[int],
    extra: dict[str, list] | None = None,
) -> None:
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator='\n')
    buf.write(
        f'# Leaves on the Line, {url}\n# {LICENCE}\n'
        '# Each row names the Network Rail release file it came from and when that came out.\n'
    )
    extra = extra or {}
    out.writerow(
        [
            'period',
            'start',
            'end',
            'days',
            'release_file',
            'released',
            'agreed_share',
            'delay_minutes',
            'knock_on_minutes',
            *[f'{g}_minutes' for g in GROUP_IDS],
            'trains_cancelled',
            *extra,
        ]
    )
    for at, period in enumerate(periods):
        if at not in have:
            continue
        total = page.total[at]
        out.writerow(
            [
                period['id'],
                period['start'],
                period['end'],
                period['days'],
                period['file'],
                period['released'],
                round(1 - page.unagreed[at] / total, 3) if total else '',
                round(total, 1),
                round(page.knock[at], 1),
                *[round(page.minutes[g][at], 1) for g in GROUP_IDS],
                sum(page.cancelled[g][at] for g in GROUP_IDS),
                *[v[at] for v in extra.values()],
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(buf.getvalue())


def build() -> list[str]:
    for folder in ('station', 'route', 'operator', 'data'):
        shutil.rmtree(STATIC / folder, ignore_errors=True)
    errors: list[str] = []
    metas = {
        p.name: json.loads((p / 'meta.json').read_text())
        for p in sorted(PERIODS.iterdir())
        if (p / 'meta.json').exists()
    }
    table = orr.table()
    periods = axis(metas, table)
    index = {p['id']: i for i, p in enumerate(periods)}
    have = {index[p] for p in metas}
    size = max(have) + 1
    last = max(have)
    stanox, reasons, ops = codes.stanox(), codes.reasons(), codes.operators()
    stations = naptan.load()

    def place(code: str):
        crs = stanox.get(code, {}).get('crs', '')
        return stations.get(crs)

    network = Page(size)
    pages: dict[str, dict[str, Page]] = {'station': {}, 'route': {}, 'operator': {}}
    sections = defaultdict(Counter)  # route -> (group, section) -> minutes
    mapped = defaultdict(lambda: defaultdict(Counter))  # period -> feature -> group -> minutes
    off = defaultdict(Counter)  # period -> group -> minutes we can't draw
    features: dict[tuple, int] = {}
    shapes: list[list] = []

    def feature(section: str):
        ends = section.split(':')
        spots = [place(e) for e in ends]
        if len(ends) == 2 and all(spots) and spots[0]['crs'] != spots[1]['crs']:
            a, b = sorted(spots, key=lambda s: s['crs'])
            key = ('line', a['crs'], b['crs'])
            shape = ['line', f'{a["name"]} to {b["name"]}', *coords(a), *coords(b)]
        elif any(spots):
            spot = next(s for s in spots if s)
            kind = 'dot' if len(ends) == 1 or all(spots) else 'ring'
            key = (kind, spot['crs'])
            shape = [kind, spot['name'], *coords(spot)]
        else:
            return None
        if key not in features:
            features[key] = len(shapes)
            shapes.append(shape)
        return features[key]

    for period, meta in metas.items():
        at, latest = index[period], index[period] == last
        for row in rollup.load(period, 'places'):
            if row['reason'] in PEOPLE:
                errors.append(f'{period}: a people code ({row["reason"]}) reached a rollup')
                continue
            side = 'nr' if row['responsible'] == 'nr' else 'op'
            group = codes.group(row['reason'], side)
            minutes = float(row['minutes'])
            info = stanox.get(row['stanox'], {})
            spot = stations.get(info.get('crs', ''))
            targets = [network, page_for(pages, 'operator', row['operator'], size)]
            if info.get('route') and info['route'] not in ('NONE', 'Network Rail HQ'):
                targets.append(page_for(pages, 'route', slug(route_name(info['route'])), size))
            if spot:
                targets.append(page_for(pages, 'station', spot['crs'].lower(), size))
            for target in targets:
                target.add(at, latest, group, row, minutes)
        if abs(network.total[at] - meta['minutes']) > 1:
            errors.append(
                f'{period}: pages sum to {network.total[at]:.0f}, file to {meta["minutes"]}'
            )
        for row in rollup.load(period, 'sections'):
            if row['reason'] in PEOPLE:
                errors.append(f'{period}: a people code ({row["reason"]}) reached a rollup')
                continue
            group = codes.group(row['reason'], row['side'])
            minutes = float(row['minutes'])
            if not minutes:
                continue
            first = stanox.get(row['section'].split(':')[0], {})
            if first.get('route'):
                sections[slug(route_name(first['route']))][group, row['section']] += minutes
            found = feature(row['section'])
            if found is None:
                off[period][group] += minutes
            else:
                mapped[period][found][group] += minutes

    errors += network.check('network')
    for kind, found in pages.items():
        for key, page in found.items():
            errors += page.check(f'{kind} {key}')
        summed = [sum(page.total[at] for page in found.values()) for at in range(size)]
        for at in have:
            off = summed[at] - network.total[at]
            if (kind == 'operator' and abs(off) > 1) or off > 1:
                errors.append(
                    f'{kind} pages sum to {summed[at]:.0f} in period {at}, '
                    f'the network to {network.total[at]:.0f}'
                )
    if errors:
        return errors

    def label(section: str) -> str:
        names = []
        for end in section.split(':'):
            spot = place(end)
            names.append(spot['name'] if spot else title(stanox.get(end, {}).get('name', end)))
        return ' to '.join(names)

    routes = {
        slug(route_name(r['route'])): route_name(r['route'])
        for r in stanox.values()
        if r['route'] and slug(route_name(r['route'])) in pages['route']
    }
    for key, page in pages['route'].items():
        worst = {
            g: [
                [label(s), round(m, 1)]
                for (gg, s), m in sorted(sections[key].items(), key=lambda kv: -kv[1])
                if gg == g
            ][:10]
            for g in GROUP_IDS
        }
        data = {
            'kind': 'route',
            'id': key,
            'name': routes[key],
            **page.json(have, reasons),
            'sections': {g: rows for g, rows in worst.items() if rows},
        }
        publish('route', key, data, page, periods, have)

    by_code = {op['code']: op for op in ops.values()}
    orr_by_name = {op['orr']: op['code'] for op in ops.values()}
    gaps = [i for i in range(len(periods)) if i not in have]
    orr_series = defaultdict(lambda: defaultdict(lambda: [None] * len(periods)))
    for i in gaps:
        for name, cells in table.get(periods[i]['id'], {}).items():
            for who in ('network', orr_by_name.get(name)):
                if who:
                    for g in ORR_GROUPS:
                        cell = sum(v for c, v in cells.items() if c.endswith(' ' + orr.SUFFIX[g]))
                        series = orr_series[who][g]
                        series[i] = round((series[i] or 0) + cell, 1)
    for code, page in pages['operator'].items():
        op = by_code[code]
        data = {
            'kind': 'operator',
            'id': op['slug'],
            'code': code,
            'name': op['name'],
            'former': op['former'],
            **page.json(have, reasons),
            'responsible': {r: page.series(page.resp[r], have) for r in ('self', 'nr', 'other')},
            'orr': dict(orr_series[code]),
        }
        extra = {
            f'{r}_minutes': [round(v, 1) for v in page.resp[r]] for r in ('self', 'nr', 'other')
        }
        publish('operator', op['slug'], data, page, periods, have, extra)

    quiet_line = QUIET * len(have)
    for crs, page in pages['station'].items():
        spot = stations[crs.upper()]
        info = next(r for r in stanox.values() if r['crs'] == crs.upper())
        data = {
            'kind': 'station',
            'id': crs,
            'crs': crs.upper(),
            'name': spot['name'],
            'route': route_name(info['route']),
            'lat': float(spot['lat']),
            'lon': float(spot['lon']),
            'quiet': sum(page.total) < quiet_line,
            **page.json(have, reasons),
        }
        publish('station', crs, data, page, periods, have)

    write_map(mapped, off, shapes, periods, metas)
    write_json(
        STATIC / 'data' / 'index.json',
        {
            'periods': periods,
            'last': last,
            'stations': len(pages['station']),
            'taken': json.loads((DATA / 'taken.json').read_text()),
            'groups': [
                {'id': g, 'label': lab, 'orr': o, 'side': s} for g, (lab, o, s) in GROUPS.items()
            ],
            'routes': sorted(
                [{'id': k, 'name': v} for k, v in routes.items()], key=lambda r: r['name']
            ),
            'operators': sorted(
                [
                    {'id': op['slug'], 'name': op['name']}
                    for code, op in by_code.items()
                    if code in pages['operator']
                ],
                key=lambda o: o['name'].lower(),
            ),
            'network': network.json(have, reasons)
            | {
                'total': network.series(network.total, have),
                'responsible': {
                    r: network.series(network.resp[r], have) for r in ('self', 'nr', 'other')
                },
            },
        },
    )
    write_json(
        STATIC / 'data' / 'stations.json',
        sorted(
            [
                [crs, stations[crs.upper()]['name'], round(sum(p.total))]
                for crs, p in pages['station'].items()
            ],
            key=lambda s: s[1],
        ),
    )
    write_trends(metas, periods, index, orr_series['network'])
    write_odd(metas, reasons)
    write_csv(
        STATIC / 'trends.csv',
        f'{SITE}/trends',
        network,
        periods,
        have,
        {'people_minutes': [metas.get(p['id'], {}).get('people', '') for p in periods]},
    )
    return []


def page_for(pages: dict, kind: str, key: str, size: int) -> Page:
    found = pages[kind].get(key)
    if found is None:
        found = pages[kind][key] = Page(size)
    return found


def coords(spot: dict) -> list[float]:
    return [round(float(spot['lon']), 4), round(float(spot['lat']), 4)]


def publish(kind: str, key: str, data: dict, page: Page, periods, have, extra=None) -> None:
    write_json(STATIC / kind / f'{key}.json', data)
    write_csv(STATIC / kind / f'{key}.csv', f'{SITE}/{kind}/{key}', page, periods, have, extra)


def write_map(mapped, off, shapes, periods, metas) -> None:
    folder = STATIC / 'data' / 'map'
    write_json(folder / 'features.json', shapes)
    years = defaultdict(lambda: defaultdict(Counter))
    years_off = defaultdict(Counter)

    def pack(features, missing):
        return {
            'm': [
                [f, GROUP_IDS.index(g), round(m)]
                for f, by in sorted(features.items())
                for g, m in sorted(by.items())
                if m >= 0.5
            ],
            'off': {g: round(m) for g, m in missing.items()},
        }

    for period, features in mapped.items():
        year = period[:7]
        for f, by in features.items():
            years[year][f].update(by)
        years_off[year].update(off[period])
        write_json(folder / f'{period}.json', pack(features, off[period]))
    for year, features in years.items():
        write_json(folder / f'{year}.json', pack(features, years_off[year]))


def write_trends(metas, periods, index, orr_network) -> None:
    days = Counter()
    split = defaultdict(Counter)
    for meta in metas.values():
        for day, by in meta['daily'].items():
            days[day] += sum(by.values())
            split[day].update(by)

    def worst(key):
        return [
            [d, round(days[d]), {g: round(m) for g, m in split[d].items() if m >= 1}]
            for d in sorted(days, key=key)[:20]
        ]

    write_json(
        STATIC / 'data' / 'trends.json',
        {
            'people': [metas[p['id']]['people'] if p['id'] in metas else None for p in periods],
            'orr': dict(orr_network),
            'worst': worst(lambda d: -days[d]),
            'storms': worst(lambda d: -split[d]['weather']),
        },
    )


# codes picked for the odd ones page, which ranks them by minutes
ODD = ['X8', 'I8', 'W8', 'V8', 'XP', 'WP', 'XQ', 'JI', 'XU', 'XR']
ODD += ['WR', 'JQ', 'XO', 'J6', 'X3', 'RP', 'ZB', 'OG', 'JX', 'JH']


def write_odd(metas, reasons) -> None:
    incidents, minutes = Counter(), Counter()
    words = defaultdict(lambda: [0, 0.0])
    for meta in metas.values():
        incidents.update(meta['incidents'])
        for word, (count, mins) in meta['words'].items():
            words[word][0] += count
            words[word][1] += mins
    for period in metas:
        for row in rollup.load(period, 'places'):
            if row['reason'] in ODD:
                minutes[row['reason']] += float(row['minutes'])
    found = [[c, reasons[c]['description'], incidents[c], round(minutes[c])] for c in ODD]
    write_json(
        STATIC / 'data' / 'odd.json',
        {
            'codes': sorted([code for code in found if code[3]], key=lambda r: -r[3]),
            'words': sorted([[w, n, round(m)] for w, (n, m) in words.items()], key=lambda r: -r[2]),
        },
    )
