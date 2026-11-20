import hashlib
import json
from .config import VERSION


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identify(raw):
    return digest(VERSION.encode() + b'\0' + raw)
