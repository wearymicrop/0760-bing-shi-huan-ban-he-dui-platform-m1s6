from flask import Blueprint, Response, current_app, jsonify, request
from app import manifest, source
from app.errors import InputError
from . import service

routes = Blueprint('archive', __name__)


@routes.post('/api/runs')
def run():
    if 'source' in request.files:
        document = request.files['source'].read()
    else:
        params = request.get_json(silent=True)
        if not isinstance(params, dict) or not isinstance(params.get('sample'), str):
            raise InputError('BAD_SOURCE')
        document = source.sample(params['sample'])
    bundle, reused = service.record(current_app.config['DB_PATH'], document)
    return jsonify(bundle | {'reused': reused}), 200 if reused else 201


@routes.post('/api/runs/<run_id>/rerun')
def rerun(run_id):
    path = current_app.config['DB_PATH']
    raw, _ = service.get(path, run_id)
    bundle, reused = service.record(path, raw, refresh=True)
    return jsonify(bundle | {'reused': reused})


@routes.get('/api/runs/<run_id>')
def detail(run_id):
    return jsonify(service.get(current_app.config['DB_PATH'], run_id)[1])


@routes.get('/api/runs/<run_id>/export')
def export_run(run_id):
    raw, bundle = service.get(current_app.config['DB_PATH'], run_id)
    document = bundle | {'original_json': raw.decode('utf-8')}
    return Response(manifest.encode(document), mimetype='application/json',
                    headers={'Content-Disposition': f'attachment; filename="rink-{run_id[:12]}.json"'})
