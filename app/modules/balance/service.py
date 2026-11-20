from .rules import compute


def reconcile(events, debit, quarantined):
    rows, totals, okay = compute(events, debit['rows'], debit['vouchers'])
    return {'rows': rows, 'issues': quarantined + debit['issues'], 'tally': totals, 'balanced': okay,
            'metrics': {'有效预订（分）': totals['booked'], '分钟差额': totals['difference'],
                        '权益差额': totals['voucher_difference'], '复核条目': len(quarantined) + len(debit['issues'])}}
