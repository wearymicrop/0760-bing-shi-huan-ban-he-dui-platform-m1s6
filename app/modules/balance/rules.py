from collections import defaultdict
from app.clock import minutes

BUCKETS = ('debit', 'cash', 'waived', 'disputed')


def compute(events, ledger, vouchers):
    """向后兼容的三元组：逐单差额、汇总、是否对平。"""
    rows, totals, _voucher_rows, okay = audit(events, ledger, vouchers)
    return rows, totals, okay


def audit(events, ledger, vouchers):
    tallies = defaultdict(lambda: dict.fromkeys(BUCKETS, 0))
    for row in ledger:
        for key in BUCKETS:
            tallies[row['key']][key] += row[key]
    rows = []
    for event in sorted(events, key=lambda e: (e.rink, e.start, e.key)):
        expected = minutes(event.start, event.end)
        amounts = tallies.pop(event.key, dict.fromkeys(BUCKETS, 0))
        rows.append({'line': event.line, 'key': event.key, 'rink': event.rink, 'booked': expected,
                     **amounts, 'difference': expected - sum(amounts.values())})
    for booking, amounts in sorted(tallies.items()):
        rows.append({'line': 0, 'key': booking, 'rink': '', 'booked': 0, **amounts,
                     'difference': -sum(amounts.values())})
    totals = {key: sum(row[key] for row in rows) for key in ('booked', *BUCKETS, 'difference')}
    totals['voucher_difference'] = sum(v['used'] for v in vouchers) - totals['debit']
    voucher_rows, voucher_okay = voucher_checks(ledger, vouchers)
    okay = (all(row['difference'] == 0 for row in rows) and totals['voucher_difference'] == 0
            and voucher_okay)
    return rows, totals, voucher_rows, okay


def voucher_checks(ledger, vouchers):
    """逐券对平：核发 = 已用 + 剩余，且已用 = 该券在折抵明细中的累计扣券。

    同时核对每张券的请求队列（按扣券顺序）与其已用分钟一致，便于交接时复核旧券先到先用。
    """
    by_line = defaultdict(int)
    for row in ledger:
        if row.get('voucher_line'):
            by_line[row['voucher_line']] += row['debit']
    rows = []
    for voucher in vouchers:
        awarded = by_line.get(voucher.get('line', 0), 0)
        allowed = voucher.get('allowed', 0)
        used = voucher.get('used', 0)
        remaining = voucher.get('remaining', allowed - used)
        requested = sum(item['award'] for item in voucher.get('requests', []))
        difference = allowed - (used + remaining)
        rows.append({'line': voucher.get('line', 0), 'key': voucher.get('key', ''),
                     'allowed': allowed, 'used': used,
                     'remaining': remaining, 'ledger': awarded,
                     'requests': requested, 'difference': difference,
                     'balanced': (difference == 0 and awarded == used
                                  and requested == used
                                  and 0 <= used <= allowed)})
    return rows, all(row['balanced'] for row in rows)
