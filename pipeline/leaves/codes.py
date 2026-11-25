"""What each code in the files means: cause groups, who's responsible, who's a person"""

import json
from functools import cache

from . import glossary
from .paths import DATA

# ORR's cause groups, with autumn pulled out of weather, in the order pages show them
GROUPS = {
    'track': ('Track', 'Track', 'nr'),
    'assets': ('Signals, points and power', 'Non-track assets', 'nr'),
    'weather': ('Weather and structures', 'Severe weather, autumn and structures', 'nr'),
    'autumn': ('Autumn', 'Severe weather, autumn and structures', 'nr'),
    'external': ('External', 'External', 'nr'),
    'network': ('Network management', 'Network management/other', 'nr'),
    'fleet': ('Train faults', 'Fleet', 'op'),
    'traincrew': ('Traincrew', 'Traincrew', 'op'),
    'stations': ('Stations', 'Stations', 'op'),
    'operations': ('Operations', 'Operations', 'op'),
    'op-other': ('Operator, other', 'TOC other', 'op'),
}
NR_CATEGORIES = {
    'Track': 'track',
    'Non-Track Assets': 'assets',
    'Severe Weather, Autumn & Structures': 'weather',
    'External': 'external',
    'Network Management / Other': 'network',
}
OP_CATEGORIES = {
    'Fleet': 'fleet',
    'Traincrew': 'traincrew',
    'Stations': 'stations',
    'Operations': 'operations',
    'TOC Other': 'op-other',
}

# fatalities, trespass, welfare, disorder, police searches and ill or injured passengers
PEOPLE = frozenset(['XC', 'VC', 'XA', 'WA', 'VA', 'XF', 'VG', 'XG', 'VD', 'RO', 'TE'])
DELAY = frozenset('AM')
CANCELLED = frozenset('CP')


class UnknownCode(Exception):
    pass


@cache
def operators() -> dict[str, dict]:
    return {op['code']: op for op in json.loads((DATA / 'operators.json').read_text())}


@cache
def reasons() -> dict[str, dict[str, str]]:
    return {row['code']: row for row in glossary.load('reasons')}


@cache
def managers() -> dict[str, tuple[str, str]]:
    return {row['code']: (row['org'], row['kind']) for row in glossary.load('managers')}


@cache
def stanox() -> dict[str, dict[str, str]]:
    return {row['stanox']: row for row in glossary.load('stanox')}


@cache
def calendar() -> dict[str, dict[str, str]]:
    return {row['period']: row for row in glossary.load('periods')}


def responsible(manager: str, operator: str) -> str:
    """self, nr or other. ORR counts the 'others' (contractors and the like) as Network Rail's"""
    try:
        org, kind = managers()[manager]
    except KeyError:
        raise UnknownCode(f'responsible manager {manager!r}') from None
    if kind == 'TOC/FOC':
        return 'self' if org == operator else 'other'
    return 'nr'


def group(reason: str, side: str) -> str:
    try:
        row = reasons()[reason]
    except KeyError:
        raise UnknownCode(f'incident reason {reason!r}') from None
    category = row['category']
    if category not in (*NR_CATEGORIES, *OP_CATEGORIES, 'All Others'):
        raise UnknownCode(f'category {category!r} on reason {reason}')
    if side == 'op':
        return OP_CATEGORIES.get(category, 'op-other')
    found = NR_CATEGORIES.get(category, 'network')
    return 'autumn' if found == 'weather' and row['supergroup'] == 'AG' else found
