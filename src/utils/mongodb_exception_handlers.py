from pymongo.errors import PyMongoError, DuplicateKeyError, ConnectionFailure
from flask import jsonify, Response

from src.app import app


@app.errorhandler(PyMongoError)
def handle_mongodb_exception(error: PyMongoError) -> tuple[Response, int]:
    if isinstance(error, DuplicateKeyError):
        return handle_duplicate_key_error(error)
    elif isinstance(error, ConnectionFailure):
        return handle_connection_failure_error(error)
    else:
        return jsonify(err=f"Ha ocurrido un error en MongoDB: {error}"), 500


def handle_duplicate_key_error(error: DuplicateKeyError) -> tuple[Response, int]:
    return jsonify(err=f"Error de clave duplicada en MongoDB: {error.details['keyValue']}"), 409


def handle_connection_failure_error(error: ConnectionFailure) -> tuple[Response, int]:
    return jsonify(err=f"Error de conexión con MongoDB: {error}"), 500
