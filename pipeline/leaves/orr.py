"""ORR's Table 3184, and the written-down check that our files still land on it"""

import csv
import json
import re
import statistics
from collections import defaultdict

from . import codes
from .paths import DATA, stamp
from .sources import get

URL = 'https://dataportal.orr.gov.uk/umbraco/api/databricksreport/getallreportdata?contentId=1685'
TABLE = DATA / 'orr-3184.csv'
POLICY = DATA / 'orr-policy.json'
WHO = {'nr': 'NR On TOC', 'self': 'TOC On Self', 'other': 'TOC On TOC'}
SUFFIX = {
    'track': 'Track',
    'assets': 'Non Track Assets',
    'weather': 'Severe Weather',
    'autumn': 'Severe Weather',
    'external': 'External',
    'network': 'Network Management Other',
    'fleet': 'Fleet',
    'traincrew': 'Traincrew',
    'stations': 'Stations',
    'operations': 'Operations',
    'op-other': 'TOC Other',
}
# the rule, as the spec writes it down
TOLERANCE, SETTLED, FLOOR, BAND, SHARE = 0.02, 0.94, 500, 0.10, 0.90
# our files cover everything ORR counts and a bit more, so every operator should be at least this
FLOOR_RATIO = 0.95


def column(resp: str, group: str) -> str:
    return f'{WHO[resp]} {SUFFIX[group]}'


def period_of(label: str) -> str:
    found = re.fullmatch(r'Apr (\d{4}) to Mar (\d{4}) \(Period (\d{2})\)', label)
    return f'{found[1]}-{found[2][2:]}-P{found[3]}'


def fetch() -> int:
    with get(URL) as response:
        items = json.load(response)['items']
    cells = [c for c in items[0] if c not in ('Time Period', 'Train Operating Company Name')]
    rows = sorted(
        [period_of(i['Time Period']), i['Train Operating Company Name'], *(i[c] for c in cells)]
        for i in items
    )
    before = TABLE.read_text() if TABLE.exists() else ''
    with TABLE.open('w', newline='') as fh:
        out = csv.writer(fh, lineterminator='\n')
        out.writerow(['period', 'operator', *cells])
        out.writerows(rows)
    stamp('orr', TABLE.read_text() != before)
    return len(rows)


def table() -> dict[str, dict[str, dict[str, float]]]:
    """period -> ORR operator name -> cell -> minutes"""
    out: dict = defaultdict(dict)
    with TABLE.open(newline='') as fh:
        for row in csv.DictReader(fh):
            period, name = row.pop('period'), row.pop('operator')
            out[period][name] = {cell: float(v or 0) for cell, v in row.items()}
    return out


def cells(orr: dict) -> dict[str, dict[str, float]]:
    """A rollup's (operator, responsible, group) minutes as ORR's operator by cell table"""
    out: dict = defaultdict(lambda: defaultdict(float))
    for (operator, resp, group), minutes in orr.items():
        out[operator][column(resp, group)] += minutes
    return out


def ratios(ours: dict, theirs: dict) -> dict[str, float]:
    out = {}
    for code, op in codes.operators().items():
        orr_total = sum(theirs.get(op['orr'], {}).values())
        if orr_total:
            out[code] = sum(ours.get(code, {}).values()) / orr_total
    return out


def build_policy(results: list[tuple[dict, dict, float]]) -> dict[str, float]:
    """Each operator's usual ratio to ORR, from the periods that are mostly agreed"""
    seen = defaultdict(list)
    for ours, theirs, agreed in results:
        if agreed >= SETTLED:
            for code, ratio in ratios(ours, theirs).items():
                seen[code].append(ratio)
    return {code: round(statistics.median(r), 2) for code, r in sorted(seen.items())}


def check(ours: dict, theirs: dict, agreed: float, policy: dict) -> list[str]:
    """Holds operators that only run on Network Rail's track to ORR, the rest drift too much"""
    problems = []
    names = {code: op['orr'] for code, op in codes.operators().items()}
    exact = [code for code, usual in policy.items() if usual == 1]
    for code, ratio in ratios(ours, theirs).items():
        if ratio < FLOOR_RATIO:
            problems.append(f'{names[code]} is only {ratio:.3f} of ORR, so rows have gone missing')
        elif code in exact and abs(ratio - 1) > TOLERANCE:
            problems.append(f'{names[code]} is {ratio:.3f} of ORR against its usual 1.00')
    if agreed >= SETTLED:
        big = [
            (ours.get(code, {}).get(cell, 0), v)
            for code in exact
            for cell, v in theirs.get(names[code], {}).items()
            if v > FLOOR
        ]
        close = sum(abs(mine / v - 1) <= BAND for mine, v in big)
        if big and close / len(big) < SHARE:
            problems.append(f'only {close} of {len(big)} big cells are within 10% of ORR')
    return problems
