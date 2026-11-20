from flask import Blueprint, current_app, jsonify, render_template, request
from app import source
from app.config import SAMPLES, VERSION
from app.errors import InputError
from app.modules.archive import service
from app.modulespec import MODULES

pages = Blueprint('pages', __name__)


def data(module, run_id):
    if module not in MODULES:
        raise InputError('BAD_ROW', 404)
    path = current_app.config['DB_PATH']
    bundle = service.get(path, run_id)[1] if run_id else service.record(path, source.sample('night'))[0]
    stage = service.register_view(path, bundle) if module == 'archive' else bundle['views'][module]
    return bundle, stage


@pages.get('/')
def home():
    return page('debit')


@pages.get('/desk/<module>')
def page(module):
    bundle, stage = data(module, request.args.get('run'))
    title, _, columns = MODULES[module]
    return render_template(f'{module}.html', module=module, title=title, columns=columns, run=bundle,
                           view=stage, tally=bundle['views']['balance']['tally'], modules=MODULES,
                           version=VERSION, samples=SAMPLES)


@pages.get('/api/modules/<module>/<run_id>')
def api_stage(module, run_id):
    bundle, stage = data(module, run_id)
    return jsonify({'id': bundle['id'], **stage})
