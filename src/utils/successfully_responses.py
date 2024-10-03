from flask import jsonify, Response
from bson import json_util


def resource_added_msg(resource_id: str, resource) -> tuple[Response, int]:
    return (
        jsonify(
            msg=f"El {resource} {resource_id} ha sido añadido de forma satisfactoria"
        ),
        200,
    )


def resource_deleted_msg(resource_id: str, resource) -> tuple[Response, int]:
    return (
        jsonify(
            msg=f"El {resource} {resource_id} ha sido eliminado de forma satisfactoria"
        ),
        200,
   )


def db_json_response(data):
    response = json_util.dumps(data)
    return response, 200
