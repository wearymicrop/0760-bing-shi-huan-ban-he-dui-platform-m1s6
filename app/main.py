from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from .config import DATABASE, MAX_BYTES
from .errors import InputError
from .modules.archive.handler import routes
from .reasons import MESSAGES
from .web import pages


def create_app(database=DATABASE):
    app = Flask(__name__)
    app.config.update(DB_PATH=database, MAX_CONTENT_LENGTH=MAX_BYTES + 16_384)
    app.register_blueprint(routes)
    app.register_blueprint(pages)

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.errorhandler(InputError)
    def problem(error):
        return jsonify(code=error.code, message=MESSAGES[error.code]), error.status

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return problem(InputError('SOURCE_LIMIT', 413))

    return app
