from dataclasses import dataclass
from datetime import datetime
from app.clock import interval
from app.errors import InputError
from app.source import identifier

KINDS = {'paid': '收费', 'waived': '豁免'}


@dataclass(frozen=True)
class Window:
    line: int
    rink: str
    start: datetime
    end: datetime
    kind: str

    @classmethod
    def read(cls, line, row):
        rink = identifier(row, 'rink')
        start, end = interval(row)
        kind = identifier(row, 'kind')
        if kind not in KINDS:
            raise InputError('BAD_ROW')
        return cls(line, rink, start, end, kind)

    def export(self):
        return {'line': self.line, 'key': self.rink, 'start': self.start.isoformat(),
                'end': self.end.isoformat(), 'kind': KINDS[self.kind]}


def resolve(windows, rink, start, end):
    active = tuple(w for w in windows if w.rink == rink and w.start <= start < w.end and end <= w.end)
    if not active:
        return '', 'NOT_OPEN', []
    if len({w.kind for w in active}) > 1:
        return '', 'WINDOW_OVERLAP', [w.line for w in active]
    return active[0].kind, '', [w.line for w in active]
