from leaves.cli import newest


def staged(content, released='2026-11-05', period='2026-27-P05'):
    return {'period': period, 'released': released, 'content': content, 'sha256': content}


def test_the_newest_release_of_a_period_wins():
    best, clashes = newest([staged('a', '2026-10-01'), staged('b', '2026-11-05')])
    assert best['2026-27-P05']['content'] == 'b' and clashes == []


def test_identical_copies_of_one_release_are_fine():
    best, clashes = newest([staged('a'), staged('a')])
    assert list(best) == ['2026-27-P05'] and clashes == []


def test_two_different_files_claiming_one_release_are_refused():
    best, clashes = newest([staged('a'), staged('b')])
    assert best == {} and clashes == [
        '2026-27-P05: 2 different files all say they are the 2026-11-05 release'
    ]
