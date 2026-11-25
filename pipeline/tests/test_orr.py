from leaves import orr

POLICY = {'EF': 1.0, 'HY': 1.0, 'EX': 1.13}
GWR, SWR, LIZZIE = 'Great Western Railway', 'South Western Railway', 'Elizabeth line'


def table(gwr=1000.0, swr=1000.0, lizzie=1000.0, cell=600.0):
    def op(total):
        return {'NR On TOC Track': cell, 'NR On TOC External': total - cell}

    return {GWR: op(gwr), SWR: op(swr), LIZZIE: op(lizzie)}


def ours(gwr=1000.0, swr=1000.0, lizzie=1000.0, cell=600.0):
    return {
        code: {'NR On TOC Track': cell, 'NR On TOC External': total - cell}
        for code, total in (('EF', gwr), ('HY', swr), ('EX', lizzie))
    }


def test_matching_totals_pass():
    assert orr.check(ours(), table(), 0.97, POLICY) == []


def test_an_operator_on_network_rail_track_drifting_fails():
    problems = orr.check(ours(gwr=1030), table(), 0.80, POLICY)
    assert problems == ['Great Western Railway is 1.030 of ORR against its usual 1.00']


def test_operators_partly_off_network_rail_track_are_left_alone():
    assert orr.check(ours(lizzie=1900), table(), 0.97, POLICY) == []


def test_causes_moving_between_cells_fail_once_a_period_is_agreed():
    shifted = ours(cell=300)
    assert orr.check(shifted, table(), 0.80, POLICY) == []
    assert orr.check(shifted, table(), 0.97, POLICY) == [
        'only 0 of 2 big cells are within 10% of ORR'
    ]


def test_periods_read_off_orr_labels():
    assert orr.period_of('Apr 2023 to Mar 2024 (Period 08)') == '2023-24-P08'
