from datetime import datetime, timezone
import json
from time import monotonic_ns
from app import manifest, pipeline, store
from app.config import VERSION
from app.errors import InputError


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
    created = datetime.now(timezone.utc).isoformat()
    bundle = {'id': run_id, 'manifest': {'input_sha256': manifest.digest(raw), 'result_sha256': result_hash,
              'version': VERSION, 'created_at': created, 'cutoff': views['changes']['cutoff'],
              'elapsed_ms': (monotonic_ns() - started) // 1_000_000}, 'views': views}
    saved, reused = store.save(path, run_id, raw, manifest.encode(bundle), created)
    return json.loads(saved), reused


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
