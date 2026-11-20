from datetime import datetime, time, timedelta
from .config import ZONE
from .errors import InputError


def stamp(text):
    if not isinstance(text, str):
        raise InputError('BAD_TIME')
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise InputError('BAD_TIME') from exc
    if dt.tzinfo is None or dt.second or dt.microsecond or dt.utcoffset() % timedelta(minutes=1):
        raise InputError('BAD_TIME')
    return dt.astimezone(ZONE)


def interval(row):
    start, end = stamp(row.get('start')), stamp(row.get('end'))
    if end <= start or end - start > timedelta(days=7):
        raise InputError('BAD_INTERVAL')
    return start, end


def midnights(start, end):
    day = start.date() + timedelta(days=1)
    while (point := datetime.combine(day, time.min, ZONE)) < end:
        yield point
        day += timedelta(days=1)


def minutes(start, end):
    return (end - start) // timedelta(minutes=1)
