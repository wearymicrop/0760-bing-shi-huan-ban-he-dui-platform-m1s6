import pytest
from app.main import create_app
from app.pipeline import process
from app.source import read, sample


@pytest.fixture(scope='session')
def night():
    return read(sample('night'))


@pytest.fixture(scope='session')
def ledger():
    return process(sample('night'))


@pytest.fixture
def client(tmp_path):
    return create_app(tmp_path/'archive.db').test_client()
