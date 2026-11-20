from app.pipeline import process
from app.source import sample


def test_midnight_decides_version(ledger):  # 朴素的整单折抵会错误扣完旧券
    rows = [r for r in ledger['debit']['rows'] if r['key']=='0042']
    assert [(r['day'],r['voucher'],r['debit'],r['cash']) for r in rows] == [
        ('2026-11-20','00041',20,0),('2026-11-21','00042',10,10)]


def test_adjacent_booking_cannot_reuse_depleted_voucher(ledger):
    rows = [r for r in ledger['debit']['rows'] if r['key']=='0043']
    assert [(r['cash'],r['codes']) for r in rows] == [(20,['LIMIT'])]


def test_waiver_does_not_consume_allowance(ledger):
    assert sum(x['waived'] for x in ledger['debit']['rows'] if x['key']=='0044') == 20
    voucher = next(x for x in ledger['debit']['vouchers'] if x['key']=='00072')
    assert voucher['used'] == 20 and voucher['remaining'] == 10


def test_missing_calendar_is_disputed(ledger):
    result = next(x for x in ledger['debit']['rows'] if x['key']=='0047')
    assert result['disputed'] == 10 and result['codes'] == ['NOT_OPEN']


def test_rink_overlap_blocks_both_not_neighbors(ledger):
    disputes = [(r['key'],r['disputed'],r.get('peers')) for r in ledger['debit']['rows'] if 'COLLISION' in r['codes']]
    assert disputes == [('0048',20,[11]),('0049',20,[10])]


def test_clean_ledger_no_unsettled_minutes():
    summary = process(sample('clean'))['debit']['totals']
    assert summary == {'debit':30, 'cash':30, 'waived':0, 'disputed':0}
