from datetime import datetime, timezone
import json
from time import monotonic_ns
from app import manifest, pipeline, store
from app.config import VERSION
from app.errors import InputError


def refusal(views):
    """对平检查：未对平的批次不得成为正式凭证。

    返回阻止出具凭证的原因；全部通过时返回 ``None``。检查覆盖逐单分钟守恒、
    券的核发 = 已用 + 剩余、已用与折抵明细一致，以及全场扣券总数等于券已用总数。
    """
    balance = views['balance']
    checks = balance['checks']
    if checks['per_order'] and checks['per_voucher'] and checks['voucher_total']:
        return None
    return {'code': 'UNBALANCED',
            'tally': balance['tally'],
            'checks': checks,
            'shortfalls': [{'key': row['key'], 'difference': row['difference']}
                           for row in balance['rows'] if row['difference']],
            'vouchers': [{'key': row['key'], 'difference': row['difference']}
                         for row in balance['vouchers'] if not row['balanced']]}


def record(path, raw, refresh=False):
    run_id = manifest.identify(raw)
    previous = store.find(path, run_id)
    if previous and not refresh:
        return json.loads(previous[1]), True
    started = monotonic_ns()
    views = pipeline.process(raw)
    result_hash = manifest.digest(manifest.encode(views).encode())
    if previous:
        saved = json.loads(previous[1])
        if result_hash != saved['manifest']['result_sha256']:
            raise RuntimeError('同版算式复算异常')
        return saved, True
    blocked = refusal(views)
    created = datetime.now(timezone.utc).isoformat()
    bundle = {'id': run_id, 'manifest': {'input_sha256': manifest.digest(raw), 'result_sha256': result_hash,
              'version': VERSION, 'created_at': created, 'cutoff': views['changes']['cutoff'],
              'elapsed_ms': (monotonic_ns() - started) // 1_000_000,
              'balanced': blocked is None}, 'views': views}
    saved, reused = store.save(path, run_id, raw, manifest.encode(bundle), created)
    return json.loads(saved), reused


def credential(path, run_id):
    """出具正式凭证；未对平或封存记录被改动时拒绝。"""
    raw, bundle = get(path, run_id)
    if bundle['manifest'].get('balanced') is not True:
        raise InputError('UNBALANCED', 409)
    document = bundle | {'original_json': raw.decode('utf-8')}
    if manifest.digest(manifest.encode(document['views']).encode()) != bundle['manifest']['result_sha256']:
        raise InputError('UNBALANCED', 409)
    return document


def verify(path, run_id):
    """对复核凭证的复算：只读原字节重跑，不新增批次、不追加扣券。"""
    raw, bundle = get(path, run_id)
    views = pipeline.process(raw)
    result_hash = manifest.digest(manifest.encode(views).encode())
    same_result = result_hash == bundle['manifest']['result_sha256']
    balance = views['balance']
    return {'id': run_id, 'same_result': same_result,
            'input_sha256': manifest.digest(raw),
            'balance_balanced': balance['balanced'],
            'checks': balance['checks'], 'tally': balance['tally'],
            'credential': bundle['manifest'].get('balanced') is True and same_result and balance['balanced']}


def get(path, run_id):
    stored = store.find(path, run_id)
    if not stored:
        raise InputError('RUN_MISSING', 404)
    return stored[0], json.loads(stored[1])


def register_view(path, bundle):
    runs = store.history(path)
    return {'rows': [{'key': run_id[:12], 'created': created, 'run_id': run_id} for run_id, created in runs],
            'issues': [], 'metrics': {'已归档': len(runs), '输入字节': len(get(path,bundle['id'])[0])},
            'manifest': bundle['manifest']}
