from .rules import audit


def _basis_text(basis):
    return '；'.join(f"{item['code']} {item['minutes']} 分" +
                     (f"（券 {', '.join(map(str, item['passes']))}）" if item['passes'] else '') +
                     (f"（营业窗 {', '.join(map(str, item['windows']))}）" if item['windows'] else '') +
                     (f"（相交订单 {', '.join(map(str, item['peers']))}）" if item['peers'] else '')
                     for item in basis)


def reconcile(events, debit, quarantined):
    rows, totals, vouchers, okay = audit(events, debit['rows'], debit['vouchers'])
    settlements = debit.get('settlements', [])
    by_key = {item['key']: item for item in settlements}
    for row in rows:
        item = by_key.get(row['key'], {})
        row['versions'] = ', '.join(v['key'] for v in item.get('versions', [])) or '—'
        row['unredeemed'] = item.get('unredeemed', 0)
        row['basis'] = _basis_text(item.get('basis', [])) or '—'
        row['contested_with'] = ', '.join(map(str, item.get('contested_with', []))) or '—'
        row['state'] = item.get('state', '复核')
    per_order = all(row['difference'] == 0 for row in rows)
    per_voucher = all(row['balanced'] for row in vouchers)
    return {'rows': rows, 'vouchers': vouchers, 'settlements': settlements,
            'issues': quarantined + debit['issues'], 'tally': totals, 'balanced': okay,
            'checks': {'per_order': per_order, 'per_voucher': per_voucher,
                       'voucher_total': totals['voucher_difference'] == 0,
                       'orders': len(rows), 'vouchers': len(vouchers)},
            'policy': debit.get('policy', {}), 'ruling': debit.get('ruling', {}),
            'metrics': {'有效预订（分）': totals['booked'], '分钟差额': totals['difference'],
                        '权益差额': totals['voucher_difference'], '复核条目': len(quarantined) + len(debit['issues'])}}
