from app import clock
from app.modules.bookings import service
from app.modules.changes import rules


def test_unordered_replay_uses_revision_time(night):  # TRAP-13
    events,_ = service.load(night['events'])
    active,_,_ = rules.resolve(events[::-1], clock.stamp(night['cutoff']))
    row = next(e for e in active if e.key == '0042')
    assert row.revision == 2 and row.line == 1 and row.start.hour == 23


def test_late_cancellation_cannot_rewrite_published_view(ledger):  # TRAP-26
    changes = ledger['changes']
    assert any(x['key']=='0042' and x['code']=='AFTER_CLOSE' and x['line']==4 for x in changes['issues'])
    assert any(row['key']=='0042' for row in changes['rows'])


def test_same_revision_disagreement_cannot_win_by_last_write(ledger):  # TRAP-14
    conflict = next(x for x in ledger['changes']['issues'] if x['code']=='REV_CONFLICT')
    assert conflict['key'] == '0051' and conflict['lines'] == [13,14]
    assert not any(x['key']=='0051' for x in ledger['changes']['rows'])


def test_cancelled_booking_no_occupancy(ledger):
    assert any(x['key']=='0052' and x['code']=='CANCELED' for x in ledger['changes']['issues'])
    assert not any(x['key']=='0052' for x in ledger['debit']['rows'])


def test_unrooted_move_is_held(ledger):
    assert any(x['key']=='0053' and x['code']=='BAD_CHAIN' and x['lines']==[17] for x in ledger['changes']['issues'])


def test_cutoff_inclusive(night):
    data = night['events'][1] | {'timestamp':night['cutoff']}
    events,_ = service.load([data])
    valid,_,issues = rules.resolve(events, clock.stamp(night['cutoff']))
    assert [r.key for r in valid] == ['0042'] and not issues
