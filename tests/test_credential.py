import json
import sqlite3
from app.modules.archive import service
from app.source import sample


def _tamper(path, run_id, mutate):
    with sqlite3.connect(path) as db:
        raw, = db.execute('SELECT bundle FROM shifts WHERE id=?', (run_id,)).fetchone()
        bundle = json.loads(raw)
        mutate(bundle)
        db.execute('UPDATE shifts SET bundle=? WHERE id=?',
                   (json.dumps(bundle, ensure_ascii=False), run_id))
        db.commit()


def test_balanced_run_exports_credential(tmp_path):
    path = tmp_path/'shifts.db'
    bundle, _ = service.record(path, sample('clean'))
    assert bundle['manifest']['balanced'] is True
    document = service.credential(path, bundle['id'])
    assert document['views']['balance']['balanced'] and document['original_json']


def test_unbalanced_flag_blocks_credential(tmp_path):
    path = tmp_path/'shifts.db'
    bundle, _ = service.record(path, sample('clean'))
    _tamper(path, bundle['id'], lambda b: b['manifest'].update(balanced=False))
    try:
        service.credential(path, bundle['id'])
    except Exception as exc:  # noqa: BLE001 - 断言领域错误
        assert getattr(exc, 'code', '') == 'UNBALANCED' and getattr(exc, 'status', 0) == 409
    else:
        raise AssertionError('未对平批次不应出具凭证')


def test_changed_views_block_credential(tmp_path):
    path = tmp_path/'shifts.db'
    bundle, _ = service.record(path, sample('clean'))

    def drift(document):
        document['views']['balance']['rows'][0]['cash'] -= 1

    _tamper(path, bundle['id'], drift)
    try:
        service.credential(path, bundle['id'])
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, 'code', '') == 'UNBALANCED'
    else:
        raise AssertionError('结果摘要不符不应出具凭证')


def test_refusal_names_shortfallen_order_and_voucher(tmp_path):
    from app.modules.archive.service import refusal
    from app.pipeline import process
    views = process(sample('clean'))
    views['balance']['checks']['per_order'] = False
    views['balance']['rows'][0]['difference'] = 3
    blocked = refusal(views)
    assert blocked['code'] == 'UNBALANCED'
    assert {'key': views['balance']['rows'][0]['key'], 'difference': 3} in blocked['shortfalls']


def test_rerun_does_not_add_vouchers_or_charge_again(tmp_path):
    path = tmp_path/'shifts.db'
    first, _ = service.record(path, sample('night'))
    second, reused = service.record(path, sample('night'), refresh=True)
    assert reused and first == second
    assert sum(v['used'] for v in second['views']['debit']['vouchers']) == second['views']['balance']['tally']['debit']
    assert len(second['views']['debit']['vouchers']) == len(first['views']['debit']['vouchers'])


def test_export_returns_409_for_unbalanced(client, tmp_path):
    created = client.post('/api/runs', json={'sample': 'clean'}).json
    path = client.application.config['DB_PATH']
    _tamper(path, created['id'], lambda b: b['manifest'].update(balanced=False))
    response = client.get(f"/api/runs/{created['id']}/export")
    assert response.status_code == 409 and response.json['code'] == 'UNBALANCED'
