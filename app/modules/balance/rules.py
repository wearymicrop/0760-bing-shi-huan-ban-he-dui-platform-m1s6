from collections import defaultdict
from app.clock import minutes

BUCKETS = ('debit', 'cash', 'waived', 'disputed')


def compute(events, ledger, vouchers):
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
    okay = (all(row['difference'] == 0 for row in rows) and totals['voucher_difference'] == 0
            and all(0 <= v['used'] <= v['allowed'] and v['used'] + v['remaining'] == v['allowed'] for v in vouchers))
    return rows, totals, okay
