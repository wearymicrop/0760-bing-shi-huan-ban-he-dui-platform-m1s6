from app import clock
from app.modules.passes import rules, service


def test_initial_zero_preserved(ledger):  # TRAP-08
    assert ledger['passes']['rows'][0]['key'] == '00041'


def test_negative_allowance_isolated(ledger):
    assert ledger['passes']['issues'][0]['line'] == 7
    assert ledger['passes']['issues'][0]['code'] == 'BAD_ROW'


def test_bool_is_not_an_allowance(night):
    _, result = service.load([night['passes'][0] | {'allowance': True}])
    assert result['issues'][0]['raw']['allowance'] is True
    assert result['rows'] == []


def test_overlapping_entitlements_hold_minutes(night):  # TRAP-25
    records, _ = service.load(night['passes'])
    a,b = map(clock.stamp, ['2026-11-21T00:20:00+08:00','2026-11-21T00:40:00+08:00'])
    assert rules.resolve(records,'飞雪','南冰',a,b) == (None,'PASS_OVERLAP',[4,5])


def test_no_pass_evidence_not_zero_allowance(night):
    records,_ = service.load(night['passes'])
    a,b = map(clock.stamp, ['2026-11-21T02:20:00+08:00','2026-11-21T02:40:00+08:00'])
    assert rules.resolve(records,'飞雪','西冰',a,b) == (None,'NO_PASS',[])


def test_duplicate_pass_does_not_add_budget(night):
    record=night['passes'][0]
    versions, view = service.load([record, record])
    assert sum(v.allowance for v in versions) == 25
    assert view['issues'][0]['code'] == 'DUP_PASS'
