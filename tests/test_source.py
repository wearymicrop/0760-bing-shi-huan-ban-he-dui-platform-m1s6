import pytest
from app import source
from app.errors import InputError


def test_bom_reads_without_affecting_facts():  # TRAP-02
    original = source.sample('night')
    assert source.read(b'\xef\xbb\xbf' + original) == source.read(original)


def test_exchange_rejects_empty_arrays():
    with pytest.raises(InputError, match='EMPTY_SOURCE'):
        source.read(b'{"windows":[],"passes":[],"events":[]}')


def test_file_payload_limit_before_parsing():
    with pytest.raises(InputError, match='SOURCE_LIMIT') as caught:
        source.read(b'x'*(source.MAX_BYTES+1))
    assert caught.value.status == 413
