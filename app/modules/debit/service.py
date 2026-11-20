from collections import Counter
from app.clock import minutes
from app.modules.calendar.rules import resolve as availability
from app.modules.passes.rules import resolve as entitlement
from app.reasons import evidence
from .partition import boundaries, collisions

LABELS = {'debit': '扣券', 'cash': '自付', 'waived': '豁免', 'disputed': '争议'}


def allocate(events, windows, versions):
    collided = collisions(events)
    usage = Counter()
    totals = Counter({key: 0 for key in LABELS})
    ledger, issues = [], []

    def add(event, start, end, stage, amount, codes=(), **references):
        for key, count in zip(LABELS, amount):
            totals[key] += count
        item = dict(zip(LABELS, amount))
        ledger.append({'line': event.line, 'key': event.key, 'rink': event.rink, 'day': start.date().isoformat(),
                       'start': start.isoformat(), 'end': end.isoformat(),
                       'status': '折抵与自付' if item['debit'] and item['cash'] else LABELS[stage],
                       'stage': stage, 'codes': [code for code in codes if code], **item, **references})
        issues.extend(evidence(code, event.line, event.key, minutes=minutes(start, end), **references)
                      for code in codes if code and stage == 'disputed')

    for event in sorted(events, key=lambda e: (e.start, e.rink, e.key)):
        edges = boundaries(event, windows, versions)
        for start, end in zip(edges, edges[1:]):
            count = minutes(start, end)
            if peers := collided.get(event.key):
                add(event, start, end, 'disputed', (0, 0, 0, count), ('COLLISION',), peers=peers)
                continue
            kind, warning, window_lines = availability(windows, event.rink, start, end)
            if warning:
                add(event, start, end, 'disputed', (0, 0, 0, count), (warning,), windows=window_lines)
                continue
            if kind == 'waived':
                add(event, start, end, 'waived', (0, 0, count, 0), windows=window_lines)
                continue
            version, warning, pass_lines = entitlement(versions, event.owner, event.rink, start, end)
            if warning == 'PASS_OVERLAP':
                add(event, start, end, 'disputed', (0, 0, 0, count), (warning,), passes=pass_lines, windows=window_lines)
                continue
            spent = 0
            if version:
                spent = min(count, version.allowance - usage[version.line])
                usage[version.line] += spent
            code = warning or ('LIMIT' if spent < count else '')
            add(event, start, end, 'debit' if spent else 'cash', (spent, count - spent, 0, 0), (code,),
                passes=pass_lines, windows=window_lines, voucher=version.key if version else '')
    balances = [{'line': v.line, 'key': v.key, 'owner': v.owner, 'allowed': v.allowance,
                 'used': usage[v.line], 'remaining': v.allowance - usage[v.line]} for v in versions]
    return {'rows': ledger, 'issues': issues, 'totals': dict(totals), 'vouchers': balances,
            'metrics': {f'{label}（分）': totals[key] for key, label in LABELS.items()}}
