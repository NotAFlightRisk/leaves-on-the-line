import csv
import io
import zipfile

import pytest

from leaves import codes, rollup

NEW = [
    'FINANCIAL_YEAR_PERIOD',
    'ORIGIN_DEPARTURE_DATE',
    'TRUST_TRAIN_ID',
    'TOC_CODE',
    'INCIDENT_NUMBER',
    'INCIDENT_CREATE_DATE',
    'SECTION_CODE',
    'RESPONSIBLE_MANAGER',
    'INCIDENT_REASON',
    'ATTRIBUTION_STATUS',
    'INCIDENT_DESCRIPTION',
    'REACT_REASON',
    'EVENT_TYPE',
    'START_STANOX',
    'EVENT_DATETIME',
    'PFPI_MINUTES',
]
OLD = {
    'FINANCIAL_YEAR_PERIOD': 'FINANCIAL_YEAR_AND_PERIOD',
    'TRUST_TRAIN_ID': 'TRUST_TRAIN_ID_AFFECTED',
    'TOC_CODE': 'OPERATOR_AFFECTED',
    'REACT_REASON': 'REACTIONARY_REASON_CODE',
    'EVENT_TYPE': 'PERFORMANCE_EVENT_CODE',
}
NR = next(code for code, (_, kind) in codes.managers().items() if kind == 'Network Rail')
GWR = next(code for code, (org, kind) in codes.managers().items() if org == 'EF')


def row(**given):
    base = dict(
        FINANCIAL_YEAR_PERIOD='2023/24_P08',
        ORIGIN_DEPARTURE_DATE='20-OCT-23',
        TRUST_TRAIN_ID='1A01',
        TOC_CODE='EF',
        INCIDENT_NUMBER='1',
        INCIDENT_CREATE_DATE='20-OCT-2023 00:00',
        SECTION_CODE='73000:73100',
        RESPONSIBLE_MANAGER=NR,
        INCIDENT_REASON='IB',
        ATTRIBUTION_STATUS='Attribution Agreed',
        INCIDENT_DESCRIPTION='POINTS FAILURE',
        REACT_REASON='',
        EVENT_TYPE='A',
        START_STANOX='73000',
        EVENT_DATETIME='20-OCT-2023 08:00',
        PFPI_MINUTES='10',
    )
    return base | given


def book(rows, header=NEW, trailer=False):
    buf = io.StringIO()
    out = csv.writer(buf)
    out.writerow(header)
    for r in rows:
        out.writerow(r[name] for name in NEW)
    if trailer:
        out.writerow([f'EOF: {len(rows)}'])
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('period.csv', buf.getvalue())
    return zipfile.ZipFile(data)


def rolled(rows, **kw):
    return rollup.roll(book(rows, **kw), 'period.csv')['2023-24-P08']


def minutes(roll):
    return sum(m for m, _, _ in roll.places.values())


def test_counts_delay_events_on_passenger_trains_only():
    roll = rolled(
        [
            row(PFPI_MINUTES='10'),
            row(
                EVENT_TYPE='M',
                PFPI_MINUTES='5',
                REACT_REASON='YD',
                ATTRIBUTION_STATUS='Attribution Disputed',
            ),
            row(EVENT_TYPE='C', PFPI_MINUTES='60', INCIDENT_NUMBER='2'),
            row(TOC_CODE='WA', PFPI_MINUTES='100'),
        ]
    )
    assert minutes(roll) == 15
    assert sum(u for _, u, _ in roll.places.values()) == 5
    assert roll.daily['2023-10-20']['assets'] == 15


def test_drops_people_incidents_by_incident_knock_on_and_all():
    roll = rolled(
        [
            row(),
            row(INCIDENT_NUMBER='9', INCIDENT_REASON='XC', PFPI_MINUTES='40'),
            row(
                INCIDENT_NUMBER='9',
                INCIDENT_REASON='IB',
                REACT_REASON='YD',
                EVENT_TYPE='M',
                PFPI_MINUTES='30',
            ),
        ]
    )
    assert minutes(roll) == 10
    assert roll.people == 70
    assert all(key[1] not in codes.PEOPLE for key in roll.places)


def test_counts_each_cancelled_train_once_per_incident():
    roll = rolled(
        [
            row(EVENT_TYPE='C', PFPI_MINUTES='0'),
            row(EVENT_TYPE='P', PFPI_MINUTES='0'),
            row(EVENT_TYPE='C', PFPI_MINUTES='0', INCIDENT_NUMBER='2'),
            row(EVENT_TYPE='C', PFPI_MINUTES='0', TRUST_TRAIN_ID='1A02'),
            row(EVENT_TYPE='C', PFPI_MINUTES='0', INCIDENT_NUMBER='', INCIDENT_REASON=''),
        ]
    )
    assert sum(c for _, _, c in roll.places.values()) == 3


def test_splits_blame_between_operators_and_network_rail():
    roll = rolled([row(), row(RESPONSIBLE_MANAGER=GWR, INCIDENT_REASON='MD', INCIDENT_NUMBER='3')])
    sides = {key[3]: m for key, (m, _, _) in roll.places.items()}
    assert sides == {'nr': 10, 'self': 10}


def test_reads_the_2018_column_names_and_skips_the_trailer():
    header = [OLD.get(name, name) for name in NEW]
    roll = rolled([row(FINANCIAL_YEAR_PERIOD='2023/24_P08')], header=header, trailer=True)
    assert minutes(roll) == 10


def test_counts_words_without_keeping_the_text():
    roll = rolled([row(INCIDENT_DESCRIPTION='SWANS ON LINE AT TONBRIDGE', INCIDENT_REASON='X8')])
    assert {w: len(i) for w, i in roll.word_incidents.items()} == {'swan': 1}


def test_an_unknown_reason_code_fails_loudly():
    with pytest.raises(codes.UnknownCode):
        rolled([row(INCIDENT_REASON='ZZ9')])


def test_a_missing_column_fails_loudly():
    with pytest.raises(rollup.MissingColumn):
        rolled([row()], header=[name for name in NEW if name != 'START_STANOX'] + ['SPARE'])


def test_dates_come_in_either_format():
    assert rollup.day('14-OCT-2018 18:54') == '2018-10-14'
    assert rollup.day('28/04/2019 13:25') == '2019-04-28'


def test_an_unknown_manager_fails_loudly():
    with pytest.raises(codes.UnknownCode):
        rolled([row(RESPONSIBLE_MANAGER='ZZZZ')])


def test_a_cancelled_train_lands_on_its_earliest_event_whatever_the_row_order():
    first = row(
        EVENT_TYPE='C', PFPI_MINUTES='0', START_STANOX='73000', EVENT_DATETIME='20-OCT-2023 07:00'
    )
    later = row(
        EVENT_TYPE='P', PFPI_MINUTES='0', START_STANOX='73100', EVENT_DATETIME='20-OCT-2023 09:00'
    )
    for order in ([first, later], [later, first]):
        cancelled = {key[0]: c for key, (_, _, c) in rolled(order).places.items() if c}
        assert cancelled == {'73000': 1}


def test_a_short_row_that_isnt_the_trailer_fails_loudly():
    buf = io.StringIO()
    out = csv.writer(buf)
    out.writerow(NEW)
    out.writerow([row()[name] for name in NEW])
    out.writerow(['2023/24_P08', '20-OCT-23'])
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('period.csv', buf.getvalue())
    with pytest.raises(rollup.MalformedRow):
        rollup.roll(zipfile.ZipFile(data), 'period.csv')


def test_a_padded_trailer_is_skipped_too():
    buf = io.StringIO()
    out = csv.writer(buf)
    out.writerow(NEW)
    out.writerow([row()[name] for name in NEW])
    out.writerow(['EOF: 1'] + [''] * (len(NEW) - 1))
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('period.csv', buf.getvalue())
    assert list(rollup.roll(zipfile.ZipFile(data), 'period.csv')) == ['2023-24-P08']


def test_a_record_split_inside_its_period_is_stitched_back_together():
    buf = io.StringIO()
    out = csv.writer(buf)
    out.writerow(NEW)
    out.writerow(['', '2023/24_P08'])
    out.writerow([row(FINANCIAL_YEAR_PERIOD='')[name] for name in NEW])
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('period.csv', buf.getvalue())
    roll = rollup.roll(zipfile.ZipFile(data), 'period.csv')['2023-24-P08']
    assert minutes(roll) == 10
