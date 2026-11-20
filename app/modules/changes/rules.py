from collections import defaultdict
from app.reasons import evidence


def resolve(events, cutoff):
    groups = defaultdict(lambda: defaultdict(list))
    issues, canceled, valid = [], [], []
    for event in events:
        if event.timestamp > cutoff:
            issues.append(evidence('AFTER_CLOSE', event.line, event.key, raw=event.export()))
        else:
            groups[event.key][event.revision].append(event)
    for key, revisions in sorted(groups.items()):
        chain, conflict = [], []
        for _, siblings in sorted(revisions.items()):
            if len({e.payload() for e in siblings}) > 1:
                conflict.extend(e.line for e in siblings)
                continue
            ordered = sorted(siblings, key=lambda e: (e.timestamp, e.line))
            chain.append(ordered[0])
            issues.extend(evidence('DUP_EVENT', e.line, key, raw=e.export()) for e in ordered[1:])
        if conflict:
            issues.append(evidence('REV_CONFLICT', conflict[0], key, lines=conflict))
            continue
        if (chain[0].action != 'reserve' or chain[0].revision != 1 or any(e.action != 'move' for e in chain[1:-1])
                or (len(chain) > 1 and chain[-1].action == 'reserve')
                or any(b.revision != a.revision + 1 or b.timestamp < a.timestamp for a,b in zip(chain,chain[1:]))
                or len({e.owner for e in chain if e.action != 'cancel'}) > 1):
            issues.append(evidence('BAD_CHAIN', chain[-1].line, key, lines=[e.line for e in chain]))
            continue
        issues.extend(evidence('STALE_EVENT', e.line, key, revision=e.revision) for e in chain[:-1])
        latest = chain[-1]
        if latest.action == 'cancel':
            canceled.append(evidence('CANCELED', latest.line, key))
        else:
            valid.append(latest)
    return valid, canceled, issues
