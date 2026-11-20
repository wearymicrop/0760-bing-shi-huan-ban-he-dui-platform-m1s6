from app.errors import InputError
from app.reasons import evidence
from .rules import Pass


def load(rows):
    versions, issues, keys = [], [], set()
    for line, row in enumerate(rows, 1):
        try:
            if not isinstance(row, dict):
                raise InputError('BAD_ROW')
            version = Pass.read(line, row)
        except InputError as exc:
            issues.append(evidence(exc.code, line, raw=row))
            continue
        key = (version.key, version.owner, version.rink, version.start, version.end, version.allowance)
        if key in keys:
            issues.append(evidence('DUP_PASS', line, version.key, raw=row))
            continue
        keys.add(key)
        versions.append(version)
    return versions, {'rows': [v.export() for v in versions], 'issues': issues,
                      'metrics': {'版本': len(versions), '持券队': len({v.owner for v in versions}),
                                  '重复或无效': len(issues)}}
