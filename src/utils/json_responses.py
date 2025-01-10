from bson import json_util
from flask import jsonify, Response
from typing import Union


def success_json_response(resource_id: str, resource: str, action: str) -> tuple[Response, int]:
    return jsonify(msg=f"{resource.capitalize()} '{resource_id}' ha sido {action} de forma satisfactoria"), 200


def db_json_response(response: Union[list, dict]) -> tuple[Response, int]:
    return Response(json_util.dumps(response)), 200
