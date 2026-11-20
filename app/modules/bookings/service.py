from app.errors import InputError
from app.reasons import evidence
from .events import Event


def load(rows):
    events, issues, seen = [], [], set()
    for line, row in enumerate(rows, 1):
        try:
            if not isinstance(row, dict):
                raise InputError('BAD_ROW')
            event = Event.read(line, row)
        except InputError as exc:
            issues.append(evidence(exc.code, line, raw=row))
            continue
        if (key := (event.key, event.revision, event.timestamp, event.payload())) in seen:
            issues.append(evidence('DUP_EVENT', line, event.key, raw=row))
            continue
        seen.add(key)
        events.append(event)
    return events, {'rows': [e.export() for e in events], 'issues': issues,
                    'metrics': {'上报': len(rows), '采信': len(events), '异常': len(issues)}}
