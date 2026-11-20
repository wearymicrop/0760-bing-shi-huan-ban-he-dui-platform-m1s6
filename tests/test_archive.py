from concurrent.futures import ThreadPoolExecutor
import json
from app.manifest import digest
from app.modules.archive import service
from app.source import sample
from app.store import history


def test_archive_reuses_identity_and_original_result(tmp_path):
    path = tmp_path/'shifts.db'
    document = sample('night')
    first, reused = service.record(path, document)
    second, again = service.record(path, document, refresh=True)
    assert not reused and again and first == second and len(history(path)) == 1


def test_concurrent_publish_is_single_entry(tmp_path):
    path = tmp_path/'shifts.db'
    with ThreadPoolExecutor(max_workers=4) as workers:
        rows = list(workers.map(lambda _: service.record(path,sample('night')), range(4)))
    assert sum(not reused for _,reused in rows) == 1
    assert all(bundle==rows[0][0] for bundle,_ in rows)


def test_export_preserves_input_evidence(client):
    record = client.post('/api/runs',json={'sample':'night'}).json
    export = client.get(f"/api/runs/{record['id']}/export")
    assert 'attachment' in export.headers['Content-Disposition']
    evidence = json.loads(export.data)
    assert digest(evidence['original_json'].encode())==record['manifest']['input_sha256']
    assert evidence['views']['balance']['tally']['disputed'] == 85


def test_error_does_not_publish(client):  # TRAP-16
    from io import BytesIO
    aborted = client.post('/api/runs',data={'source': (BytesIO(b'{"windows":[{}]'), 'short.json')})
    assert aborted.status_code == 422 and aborted.json['code'] == 'BAD_SOURCE'
    assert history(client.application.config['DB_PATH']) == []


def test_unknown_archive_is_domain_404(client):
    result = client.get('/api/runs/side-not-found')
    assert result.status_code == 404 and result.json['code'] == 'RUN_MISSING'


def test_same_result_with_distinct_raw_manifest(tmp_path):
    document = sample('clean')
    path = tmp_path/'shifts.db'
    a,_ = service.record(path,document)
    b,_ = service.record(path,document+b'\n')
    assert a['id']!=b['id'] and a['manifest']['result_sha256']==b['manifest']['result_sha256']
