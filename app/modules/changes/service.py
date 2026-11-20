from .rules import resolve


def replay(events, cutoff):
    current, canceled, issues = resolve(events, cutoff)
    return current, {'rows': [e.export() for e in current], 'issues': issues + canceled,
                     'metrics': {'有效预订': len(current), '撤销': len(canceled),
                                 '变更诊断': len(issues)}, 'cutoff': cutoff.isoformat()}
