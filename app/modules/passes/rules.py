from dataclasses import dataclass
from datetime import datetime
from app.clock import interval
from app.source import identifier, natural


@dataclass(frozen=True)
class Pass:
    line: int
    key: str
    owner: str
    rink: str
    start: datetime
    end: datetime
    allowance: int

    @classmethod
    def read(cls, line, row):
        start, end = interval(row)
        return cls(line, identifier(row, 'pass'), identifier(row, 'owner'), identifier(row, 'rink'),
                   start, end, natural(row, 'allowance', 10080))

    def export(self):
        return {'line': self.line, 'key': self.key, 'owner': self.owner, 'rink': self.rink,
                'start': self.start.isoformat(), 'end': self.end.isoformat(), 'minutes': self.allowance}


def resolve(versions, owner, rink, start, end):
    active = [v for v in versions if v.owner == owner and v.rink == rink and v.start <= start and end <= v.end]
    if len(active) > 1:
        return None, 'PASS_OVERLAP', [v.line for v in active]
    if not active:
        return None, 'NO_PASS', []
    return active[0], '', [active[0].line]
