import pytest
from app import clock
from app.errors import InputError
from app.modules.calendar import rules, service


def test_duplicate_window_retains_one_row(night):
    windows, view = service.load(night['windows'])
    assert len(windows) == 7
    assert (view['issues'][0]['code'], view['issues'][0]['line']) == ('DUP_WINDOW', 8)


def test_reversed_window_isolated(ledger):
    assert [(x['line'], x['code']) for x in ledger['calendar']['issues']] == [(8, 'DUP_WINDOW'), (9, 'BAD_INTERVAL')]


def test_adjacent_boundary_has_single_owner(night):  # TRAP-23
    windows, _ = service.load(night['windows'])
    start = clock.stamp('2026-11-20T22:15:00+08:00')
    end = clock.stamp('2026-11-20T22:35:00+08:00')
    assert rules.resolve(windows,'西冰',start,end) == ('waived','',[3])


def test_contradictory_windows_numbered(night):  # TRAP-19
    windows, _ = service.load(night['windows'])
    a, b = map(clock.stamp, ['2026-11-21T02:00:00+08:00', '2026-11-21T02:10:00+08:00'])
    assert rules.resolve(windows,'北冰',a,b) == ('','WINDOW_OVERLAP',[1, 7])
    assert sorted(rules.resolve(windows[::-1],'北冰',a,b)[2]) == [1, 7]


def test_explicit_offset_maps_to_same_minute():  # TRAP-11
    a, b = map(clock.stamp, ['2026-11-20T15:40:00Z','2026-11-20T23:40:00+08:00'])
    assert a == b and a.hour == 23


def test_seconds_outside_grain_rejected():
    with pytest.raises(InputError, match='BAD_TIME'):
        clock.stamp('2026-11-20T15:40:05Z')
