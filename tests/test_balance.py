from app import clock
from app.modules.balance import rules
from app.modules.bookings import service
from app.modules.changes import rules as changes


def test_volume_control_totals(ledger):
    assert ledger['balance']['tally'] == {'booked':340,'debit':70,'cash':155,'waived':30,'disputed':85,'difference':0,'voucher_difference':0}


def test_reconciliation_records_disputed_and_canceled_separately(ledger):
    balance = ledger['balance']
    assert next(row['disputed'] for row in balance['rows'] if row['key']=='0045') == 20
    assert not any(row['key']=='0052' for row in balance['rows'])
    assert next(x for x in balance['issues'] if x['key']=='0052' and x['code']=='CANCELED')['line'] == 16


def test_additional_disconnected_ledger_row_detected(ledger):
    line = ledger['debit']['rows'][0] | {'key':'Orphan'}
    rows,tally,ok = rules.compute([], [line], [])
    assert not ok and rows[0]['key']=='Orphan' and tally['difference'] < 0


def test_cancellation_on_closed_shift_preserves_balance(ledger):
    assert ledger['balance']['balanced'] and sum(r['booked'] for r in ledger['balance']['rows']) == 340


def test_equal_net_shortfall_still_fails_per_booking(night, ledger):
    events, _ = service.load(night['events'])
    active, _, _ = changes.resolve(events, clock.stamp(night['cutoff']))
    rows = [r.copy() for r in ledger['debit']['rows']]
    target = next(r for r in rows[1:] if r['key']!=rows[0]['key'])
    rows[0]['cash'] -= 1
    target['cash'] += 1
    _, totals, ok = rules.compute(active, rows, ledger['debit']['vouchers'])
    assert not ok and totals['difference'] == 0


def test_negative_voucher_remaining_fails(ledger):
    _,tally,ok = rules.compute([], [], [dict(used=0,remaining=-1,allowed=-1)])
    assert tally['voucher_difference'] == 0 and not ok
