from app.modules.debit import service as debit
from app.modules.debit.partition import collisions
from app.modules.passes import service as passes_service
from app.modules.calendar import service as calendar_service
from app.modules.bookings import service as bookings_service
from app.modules.changes import rules as changes
from app import clock


def _world(night):
    windows, _ = calendar_service.load(night['windows'])
    versions, _ = passes_service.load(night['passes'])
    events, _ = bookings_service.load(night['events'])
    active, _, _ = changes.resolve(events, clock.stamp(night['cutoff']))
    return windows, versions, active


def test_settlement_lists_effective_versions_and_unredeemed(ledger):
    settlements = {row['key']: row for row in ledger['debit']['settlements']}
    assert [v['key'] for v in settlements['0042']['versions']] == ['00041', '00042']
    assert settlements['0042']['unredeemed'] == 10 and settlements['0042']['self_pay'] == 10
    assert settlements['0045']['unredeemed'] == 20
    assert settlements['0048']['contested_with'] == [11]


def test_disputed_order_keeps_contested_basis(ledger):
    settlement = next(row for row in ledger['debit']['settlements'] if row['key'] == '0045')
    codes = [item['code'] for item in settlement['basis']]
    assert codes == ['PASS_OVERLAP'] and settlement['basis'][0]['passes'] == [4, 5]


def test_same_input_replays_to_identical_allocation(night):
    windows, versions, active = _world(night)
    first = debit.allocate(active, windows, versions)
    second = debit.allocate(active[::-1], windows, versions)
    assert first['rows'] == second['rows']
    assert first['vouchers'] == second['vouchers']
    assert first['settlements'] == second['settlements']


def test_expiring_first_is_counterfactual_only(night, ledger):
    windows, versions, active = _world(night)
    alternative = debit.allocate(active, windows, versions, policy='expiry')
    assert ledger['debit']['ruling']['same_allocation'] in (True, False)
    assert sum(row['debit'] for row in alternative['rows']) == ledger['debit']['totals']['debit']
    assert alternative['totals'] == ledger['debit']['totals']


def test_voucher_usage_equals_ledger_per_voucher(ledger):
    for row in ledger['balance']['vouchers']:
        assert row['balanced']
        assert row['used'] == row['ledger'] and row['used'] + row['remaining'] == row['allowed']


def test_per_order_view_carries_version_and_basis(ledger):
    api_row = next(row for row in ledger['balance']['rows'] if row['key'] == '0042')
    assert api_row['versions'] == '00041, 00042'
    assert api_row['unredeemed'] == 10 and api_row['difference'] == 0
    assert 'LIMIT' in api_row['basis']


def test_ruling_keeps_both_conflict_sides(ledger):
    conflict = next(issue for issue in ledger['changes']['issues'] if issue['code'] == 'REV_CONFLICT')
    assert [record['line'] for record in conflict['records']] == [13, 14]
    assert {record['end'] for record in conflict['records']} == {
        '2026-11-20T20:20:00+08:00', '2026-11-20T20:23:00+08:00'}
