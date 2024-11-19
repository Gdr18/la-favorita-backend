from flask import jsonify, Response
from bson import json_util


def resource_msg(
    resource_id: str, resource, action, status_code=200
) -> tuple[Response, int]:
    return (
        jsonify(
            msg=f"{resource.capitalize()} '{resource_id}' ha sido {action} de forma satisfactoria"
        ),
        status_code,
    )


def db_json_response(data) -> tuple[Response, int]:
    response = json_util.dumps(data)
    return Response(response, mimetype="application/json"), 200
