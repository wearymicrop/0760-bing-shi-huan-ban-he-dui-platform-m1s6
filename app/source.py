import json
from .config import MAX_BYTES, MAX_ROWS, ROOT, SAMPLES
from .errors import InputError

KEYS = ('windows', 'passes', 'events')


def sample(name):
    if name not in SAMPLES:
        raise InputError('NO_SAMPLE', 404)
    return (ROOT / 'sample_data' / f'{name}.json').read_bytes()


def bad_constant(token):
    raise InputError('BAD_SOURCE')


def read(raw):
    if len(raw) > MAX_BYTES:
        raise InputError('SOURCE_LIMIT', 413)
    try:
        data = json.loads(raw.decode('utf-8-sig'), parse_constant=bad_constant)
    except (UnicodeError, ValueError) as exc:
        raise InputError('BAD_SOURCE') from exc
    if not isinstance(data, dict) or any(not isinstance(data.get(key), list) for key in KEYS):
        raise InputError('BAD_SOURCE')
    count = sum(len(data[key]) for key in KEYS)
    if count == 0:
        raise InputError('EMPTY_SOURCE')
    if count > MAX_ROWS:
        raise InputError('SOURCE_LIMIT', 413)
    return data


def identifier(row, field, optional=False):
    value = row.get(field, '')
    if not isinstance(value, str) or len(value.strip()) > 60 or (not optional and not value.strip()):
        raise InputError('BAD_ROW')
    return value.strip()


def natural(row, field, ceiling):
    value = row.get(field)
    if type(value) is not int or value < 1 or value > ceiling:
        raise InputError('BAD_ROW')
    return value
