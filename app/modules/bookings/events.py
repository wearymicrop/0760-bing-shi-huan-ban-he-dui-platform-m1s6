from dataclasses import dataclass
from datetime import datetime
from app.clock import interval, stamp
from app.errors import InputError
from app.source import identifier, natural


@dataclass(frozen=True)
class Event:
    line: int
    key: str
    revision: int
    timestamp: datetime
    action: str
    owner: str
    rink: str
    start: datetime | None
    end: datetime | None

    @classmethod
    def read(cls, line, row):
        action = identifier(row, 'action')
        if action not in {'reserve', 'move', 'cancel'}:
            raise InputError('BAD_ROW')
        start, end = (None, None) if action == 'cancel' else interval(row)
        return cls(line, identifier(row, 'booking'), natural(row, 'revision', 999_999),
                   stamp(row.get('timestamp')), action, identifier(row, 'owner', action == 'cancel'),
                   identifier(row, 'rink', action == 'cancel'), start, end)

    def payload(self):
        return (self.action, self.owner, self.rink, self.start, self.end)

    def export(self):
        return {'line': self.line, 'key': self.key, 'revision': self.revision,
                'time': self.timestamp.isoformat(), 'action': self.action, 'owner': self.owner,
                'rink': self.rink, 'start': self.start.isoformat() if self.start else '',
                'end': self.end.isoformat() if self.end else ''}
