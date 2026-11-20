from collections import Counter
from app.errors import InputError
from app.reasons import evidence
from .rules import Window


def load(rows):
    windows, issues, keys = [], [], set()
    for line, row in enumerate(rows, 1):
        try:
            window = Window.read(line, row) if isinstance(row, dict) else None
            if window is None:
                raise InputError('BAD_ROW')
        except InputError as exc:
            issues.append(evidence(exc.code, line, raw=row))
            continue
        key = (window.rink, window.start, window.end, window.kind)
        if key in keys:
            issues.append(evidence('DUP_WINDOW', line, window.rink, raw=row))
            continue
        keys.add(key)
        windows.append(window)
    counts = Counter(w.kind for w in windows)
    return windows, {'rows': [w.export() for w in windows], 'issues': issues,
                     'metrics': {'场地': len({w.rink for w in windows}), '计费窗': counts['paid'], '豁免窗': counts['waived']}}
