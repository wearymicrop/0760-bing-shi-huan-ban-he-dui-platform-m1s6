from collections import Counter, defaultdict
from datetime import datetime
from app.clock import ZONE, minutes
from app.modules.calendar.rules import resolve as availability
from app.modules.passes.rules import resolve as entitlement
from app.reasons import evidence
from .partition import boundaries, collisions

LABELS = {'debit': '扣券', 'cash': '自付', 'waived': '豁免', 'disputed': '争议'}

# 本班采用的兑现顺序。两方诉求在「旧券到期前先用」上其实一致：时段切分让旧券只在其
# 有效期内兑现；真正冲突的是额度不足时谁先占用。这里固定为最早开场者先占，避免
# 按源行顺序或券的剩余额度重排，从而保证同一输入得到同一分配。
POLICIES = {
    'start': {'label': '最早开场先兑现'},
    'expiry': {'label': '到期券先兑现'},
}
ADOPTED = 'start'
LATE = datetime.max.replace(tzinfo=ZONE)


def expiry(event, versions):
    """订单可触及权益中最早的失效时刻；无券的订单排在最后。"""
    ends = [v.end for v in versions
            if v.owner == event.owner and v.rink == event.rink and v.start < event.end and v.end > event.start]
    return min(ends, default=LATE)


def allocation_order(events, versions=(), policy=ADOPTED):
    """固定兑现顺序：开场时刻优先，其次冰面与订单号；不使用源行顺序。"""
    if policy == 'expiry':
        return sorted(events, key=lambda e: (expiry(e, versions), e.start, e.rink, e.key))
    return sorted(events, key=lambda e: (e.start, e.rink, e.key))


def allocate(events, windows, versions, policy=ADOPTED):
    ledger, issues, totals, usage, requests = _run(events, windows, versions, policy)
    balances = [{'line': v.line, 'key': v.key, 'owner': v.owner, 'allowed': v.allowance,
                 'used': usage[v.line], 'remaining': v.allowance - usage[v.line],
                 'requests': requests[(v.line, v.key)]} for v in versions]
    settlements = settle(events, ledger, versions, policy)
    return {'rows': ledger, 'issues': issues, 'totals': dict(totals), 'vouchers': balances,
            'settlements': settlements,
            'policy': {'adopted': policy, 'label': POLICIES[policy]['label'],
                       'order': '开场时刻、冰面、订单号', 'midnight_first': True,
                       'expiring_first': policy == 'expiry', 'overlap': '停扣并保留双方'},
            'ruling': ruling(events, windows, versions, ledger, policy, requests),
            'metrics': {f'{label}（分）': totals[key] for key, label in LABELS.items()}}


def _run(events, windows, versions, policy):
    collided = collisions(events)
    usage = Counter()
    totals = Counter({key: 0 for key in LABELS})
    ledger, issues = [], []
    requests = defaultdict(list)

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

    for event in allocation_order(events, versions, policy):
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
                requests[(version.line, version.key)].append(
                    {'order': len(requests[(version.line, version.key)]) + 1, 'booking': event.key,
                     'line': event.line, 'start': start.isoformat(), 'end': end.isoformat(),
                     'minutes': count, 'award': spent})
            code = warning or ('LIMIT' if spent < count else '')
            add(event, start, end, 'debit' if spent else 'cash', (spent, count - spent, 0, 0), (code,),
                passes=pass_lines, windows=window_lines, voucher=version.key if version else '',
                voucher_line=version.line if version else 0)
    return ledger, issues, totals, usage, requests


def settle(events, ledger, versions, policy=ADOPTED):
    """逐单结算：采用的有效券版本、未兑现分钟、争议依据与冲突另一方。

    同一订单可能跨午夜选用不同券版本，因此 ``versions`` 是按时段列出的有效版本链，
    而不是单一券号；「未兑现分钟」= 争议分钟 + 无人承担的自付分钟（没有可用券）。
    """
    by_line = defaultdict(list)
    claims = defaultdict(list)
    for row in ledger:
        by_line[row['key']].append(row)
        if row['stage'] == 'disputed' and 'COLLISION' in row['codes']:
            claims[row['key']].extend(row.get('peers') or [])
    tickets = {v.key: v for v in versions}
    rows = []
    for event in allocation_order(events, versions, policy):
        parts = sorted(by_line.get(event.key, []), key=lambda r: (r['start'], r['end']))
        versions_used, basis = [], []
        for part in parts:
            if part.get('voucher') and part['voucher'] not in versions_used:
                versions_used.append(part['voucher'])
            for code in part['codes']:
                item = {'code': code, 'start': part['start'], 'end': part['end'],
                        'minutes': part['disputed'] or part['cash'],
                        'voucher': part.get('voucher', ''),
                        'passes': part.get('passes') or [],
                        'windows': part.get('windows') or [],
                        'peers': part.get('peers') or []}
                if item['minutes']:
                    basis.append(item)
        unredeemed = sum(part['disputed'] for part in parts)
        cash = sum(part['cash'] for part in parts)
        rows.append({
            'key': event.key, 'rink': event.rink, 'owner': event.owner,
            'line': event.line, 'revision': event.revision,
            'start': event.start.isoformat(), 'end': event.end.isoformat(),
            'booked': minutes(event.start, event.end),
            'versions': [{'key': key, 'line': tickets[key].line, 'owner': tickets[key].owner,
                          'start': tickets[key].start.isoformat(), 'end': tickets[key].end.isoformat(),
                          'allowed': tickets[key].allowance} for key in versions_used if key in tickets],
            'debit': sum(part['debit'] for part in parts),
            'cash': cash, 'waived': sum(part['waived'] for part in parts),
            'disputed': unredeemed,
            # 未兑现 = 未由任何券折抵的分钟：待自付 + 争议待核
            'unredeemed': cash + unredeemed,
            'self_pay': cash,
            'basis': basis,
            'contested_with': sorted({p for p in claims.get(event.key, [])}),
            'state': '争议' if unredeemed else '已结清',
        })
    return rows


def ruling(events, windows, versions, ledger, policy, usage_requests):
    """比对本班采用的顺序与另一种诉求，给出可交接的裁决依据。

    两方诉求其实可以同时满足到「何时用哪张券」：按午夜与券版本端点切段，旧券只在其
    有效期内兑现（值班组要的），同券余额不足时最早开场的订单先占（前台要的）。
    剩下的冲突只发生在同一张券的余额上，因此按券列出兑现队列：谁先用、谁被挡下、
    被挡下的分钟转为自付或争议，都能逐条复核。

    对照顺序用同一套算式、只把排队键换成「到期券先排队」，列出会改由哪些订单自付。
    """
    other_cash = _alternative_cash(events, windows, versions, policy)
    adopted_cash = defaultdict(int)
    for row in ledger:
        adopted_cash[row['key']] += row['cash']
    shifts = [{'key': key, 'adopted': adopted_cash[key], 'alternative': other_cash.get(key, 0),
               'delta': other_cash.get(key, 0) - adopted_cash[key]}
              for key in sorted(set(adopted_cash) | set(other_cash))
              if adopted_cash[key] != other_cash.get(key, 0)]
    return {
        'adopted': policy, 'adopted_label': POLICIES[policy]['label'],
        'alternative': ADOPTED if policy != ADOPTED else 'expiry',
        'alternative_label': POLICIES[ADOPTED if policy != ADOPTED else 'expiry']['label'],
        'same_allocation': not shifts,
        'shifts': shifts,
        'basis': ('按午夜与券版本端点逐段选券：旧券只在其有效期内兑现，不侵占新券额度；'
                  '同一张券余额不足时，最早开场的订单先占，其余订单按同一规则依次自付。'
                  '撤销或改单只按截点前版本生效，晚到事件留待下班。'),
        'contention': contention(versions, ledger, usage_requests),
    }


def contention(versions, ledger, requests):
    """逐券兑现队列：按扣券顺序列出请求、获批与被挡下的分钟。"""
    tickets = {v.line: v for v in versions}
    codes = defaultdict(set)
    for row in ledger:
        if row.get('voucher_line'):
            for code in row['codes']:
                codes[row['voucher_line']].add(code)
    rows = []
    for line, queue in sorted(requests.items(), key=lambda item: item[0][0]):
        if not queue:
            continue
        ticket = tickets.get(line[0])
        rows.append({'line': line[0], 'key': line[1], 'owner': ticket.owner if ticket else '',
                     'allowed': ticket.allowance if ticket else 0,
                     'awarded': sum(item['award'] for item in queue),
                     'denied': sum(item['minutes'] - item['award'] for item in queue),
                     'codes': sorted(codes[line[0]]),
                     'queue': [dict(item, denied=item['minutes'] - item['award']) for item in queue]})
    return rows


def _alternative_cash(events, windows, versions, policy):
    other = 'expiry' if policy != 'expiry' else 'start'
    other_ledger, _, _, _, _ = _run(events, windows, versions, other)
    cash = defaultdict(int)
    for row in other_ledger:
        cash[row['key']] += row['cash']
    return cash
