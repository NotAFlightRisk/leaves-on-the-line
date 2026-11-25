"""One period's file in, two small rollups and a meta.json out"""

import calendar
import csv
import gzip
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from . import codes
from .codes import CANCELLED, DELAY, PEOPLE
from .paths import PERIODS

# every name a column has gone by since 2018
COLUMNS = {
    'period': ('FINANCIAL_YEAR_PERIOD', 'FINANCIAL_YEAR_AND_PERIOD'),
    'origin': ('ORIGIN_DEPARTURE_DATE',),
    'train': ('TRUST_TRAIN_ID', 'TRUST_TRAIN_ID_AFFECTED'),
    'operator': ('TOC_CODE', 'OPERATOR_AFFECTED'),
    'incident': ('INCIDENT_NUMBER',),
    'created': ('INCIDENT_CREATE_DATE',),
    'section': ('SECTION_CODE',),
    'manager': ('RESPONSIBLE_MANAGER', 'RESP_MANAGER'),
    'reason': ('INCIDENT_REASON',),
    'status': ('ATTRIBUTION_STATUS',),
    'text': ('INCIDENT_DESCRIPTION',),
    'react': ('REACT_REASON', 'REACTIONARY_REASON_CODE'),
    'event': ('EVENT_TYPE', 'PERFORMANCE_EVENT_CODE'),
    'start': ('START_STANOX',),
    'when': ('EVENT_DATETIME',),
    'minutes': ('PFPI_MINUTES',),
}
WORDS = {
    'swan': 'SWANS?',
    'deer': 'DEER',
    'cow': 'COWS?|CATTLE',
    'sheep': 'SHEEP',
    'horse': 'HORSES?',
    'badger': 'BADGERS?',
    'fox': 'FOX(?:ES)?',
    'dog': 'DOGS?',
    'bird': 'BIRDS?',
    'tree': 'TREES?',
    'balloon': 'BALLOONS?',
    'kite': 'KITES?',
    'trampoline': 'TRAMPOLINES?',
}
PATTERNS = {word: re.compile(rf'\b(?:{rx})\b') for word, rx in WORDS.items()}
MONTHS = {month: i for i, month in enumerate(calendar.month_abbr[1:], 1)}
PLACES = ['stanox', 'reason', 'operator', 'responsible', 'kind', 'minutes', 'unagreed', 'cancelled']
SECTIONS = ['section', 'reason', 'side', 'kind', 'minutes', 'unagreed', 'cancelled']


class MissingColumn(Exception):
    pass


def tally():
    return [0.0, 0.0, 0]


@dataclass
class Rollup:
    period: str
    places: defaultdict = field(default_factory=lambda: defaultdict(tally))
    sections: defaultdict = field(default_factory=lambda: defaultdict(tally))
    daily: defaultdict = field(default_factory=lambda: defaultdict(Counter))
    word_incidents: defaultdict = field(default_factory=lambda: defaultdict(set))
    word_minutes: Counter = field(default_factory=Counter)
    incidents: defaultdict = field(default_factory=lambda: defaultdict(set))
    # ORR's operator by cause cells, people incidents and all, for the check and nothing else
    orr: Counter = field(default_factory=Counter)
    unknown_managers: Counter = field(default_factory=Counter)
    # the whole file's minutes, every train and event, which is what the 94% line was set on
    file_minutes: float = 0.0
    file_agreed: float = 0.0
    people: float = 0.0
    rows: int = 0


def period_id(text: str) -> str | None:
    found = re.fullmatch(r'(\d{4})/(\d{2})_P(\d{2})', text.strip())
    return found and f'{found[1]}-{found[2]}-P{found[3]}'


@cache
def day(text: str) -> str:
    """EVENT_DATETIME's date, from either 14-OCT-2018 18:54 or 28/04/2019 13:25"""
    when = text.split()[0]
    if '/' in when:
        dd, mm, yy = when.split('/')
    else:
        dd, mon, yy = when.split('-')
        mm = MONTHS[mon.title()[:3]]
    year = int(yy) + (2000 if len(yy) == 2 else 0)
    return f'{year}-{int(mm):02}-{int(dd):02}'


def stanox(text: str) -> str:
    return ':'.join(part.zfill(5) for part in text.strip().split(':') if part)


def rows(book: zipfile.ZipFile, name: str):
    with book.open(name) as fh:
        reader = csv.reader(io.TextIOWrapper(fh, encoding='latin-1', newline=''))
        header = [col.strip().upper() for col in next(reader)]
        index = {}
        for key, names in COLUMNS.items():
            found = next((header.index(n) for n in names if n in header), None)
            if found is None:
                raise MissingColumn(f'{name} has no {names[0]} column')
            index[key] = found
        width = max(index.values())
        for row in reader:
            if len(row) > width:
                yield {key: row[i].strip() for key, i in index.items()}


def roll(book: zipfile.ZipFile, name: str) -> dict[str, Rollup]:
    """Every period in one CSV, which is usually one but a yearly file holds thirteen"""
    people = {(r['incident'], r['created']) for r in rows(book, name) if r['reason'] in PEOPLE}
    operators = codes.operators()
    out: dict[str, Rollup] = {}
    seen: set = set()
    words: dict = {}
    for r in rows(book, name):
        period = period_id(r['period'])
        if not period:
            continue
        roll = out.get(period) or out.setdefault(period, Rollup(period))
        raw = float(r['minutes'] or 0)
        roll.file_minutes += raw
        if r['status'].startswith('Attribution Agreed'):
            roll.file_agreed += raw
        # a cancellation nobody's put down to an incident has no cause to count it under
        if not r['incident'] or r['operator'] not in operators:
            continue
        roll.rows += 1
        incident = (r['incident'], r['created'])
        event, reason, operator = r['event'], r['reason'], r['operator']
        minutes = float(r['minutes'] or 0) if event in DELAY else 0.0
        if not minutes and event not in CANCELLED:
            continue
        resp = codes.responsible(r['manager'], operator)
        if not resp:
            roll.unknown_managers[r['manager']] += minutes
            resp = 'nr'
        side = 'nr' if resp == 'nr' else 'op'
        group = codes.group(reason, side)
        roll.orr[operator, resp, group] += minutes
        if incident in people:
            roll.people += minutes
            continue
        kind = 'r' if r['react'] else 'p'
        place = roll.places[r['start'].zfill(5), reason, operator, resp, kind]
        section = roll.sections[stanox(r['section']), reason, side, kind]
        roll.incidents[reason].add(incident)
        if incident not in words:
            text = r['text'].upper()
            words[incident] = [word for word, rx in PATTERNS.items() if rx.search(text)]
        for word in words[incident]:
            roll.word_incidents[word].add(incident)
            roll.word_minutes[word] += minutes
        if minutes:
            unagreed = 0.0 if r['status'].startswith('Attribution Agreed') else minutes
            for tallied in (place, section):
                tallied[0] += minutes
                tallied[1] += unagreed
            roll.daily[day(r['when'])][group] += minutes
        elif event in CANCELLED and ((r['origin'], r['train']), incident) not in seen:
            seen.add(((r['origin'], r['train']), incident))
            place[2] += 1
            section[2] += 1
    return out


def released(source: str, book: zipfile.ZipFile, name: str) -> str:
    """The date in a marketplace file's name, else the CSV's own date inside the zip"""
    found = re.search(r'(20\d{2})(\d{2})(\d{2})(?!\d)', Path(source).stem)
    if found:
        return f'{found[1]}-{found[2]}-{found[3]}'
    year, month, dd = book.getinfo(name).date_time[:3]
    return f'{year}-{month:02}-{dd:02}'


def write_table(path: Path, header: list[str], table: dict) -> None:
    buf = io.StringIO()
    out = csv.writer(buf, lineterminator='\n')
    out.writerow(header)
    for key in sorted(table):
        minutes, unagreed, cancelled = table[key]
        if minutes or cancelled:
            out.writerow([*key, round(minutes, 1), round(unagreed, 1), cancelled])
    with path.open('wb') as fh, gzip.GzipFile(fileobj=fh, mode='wb', mtime=0) as gz:
        gz.write(buf.getvalue().encode())


def meta(roll: Rollup, source: dict) -> dict:
    total = sum(m for m, _, _ in roll.places.values())
    unagreed = sum(u for _, u, _ in roll.places.values())
    days = codes.calendar()[roll.period]
    return {
        'period': roll.period,
        'start': days['start'],
        'end': days['end'],
        'days': int(days['days']),
        'source': source,
        'rows': roll.rows,
        'minutes': round(total, 1),
        'agreed': round(1 - unagreed / total, 4) if total else 0,
        'file_agreed': round(roll.file_agreed / roll.file_minutes, 4) if roll.file_minutes else 0,
        'people': round(roll.people, 1),
        'daily': {
            d: {g: round(m, 1) for g, m in sorted(by.items())}
            for d, by in sorted(roll.daily.items())
        },
        'words': {
            w: [len(roll.word_incidents[w]), round(roll.word_minutes[w], 1)]
            for w in WORDS
            if roll.word_incidents[w]
        },
        'incidents': {code: len(seen) for code, seen in sorted(roll.incidents.items())},
        'unknown_managers': {code: round(m, 1) for code, m in roll.unknown_managers.items()},
    }


def save(roll: Rollup, source: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    write_table(out / 'places.csv.gz', PLACES, roll.places)
    write_table(out / 'sections.csv.gz', SECTIONS, roll.sections)
    info = meta(roll, source)
    (out / 'meta.json').write_text(json.dumps(info, indent=1) + '\n')
    return info


def load(period: str, table: str):
    with gzip.open(PERIODS / period / f'{table}.csv.gz', 'rt', newline='') as fh:
        yield from csv.DictReader(fh)
