from flask import jsonify, Response
from typing import Union, Literal
from datetime import datetime
from bson.objectid import ObjectId
import json


def success_json_response(
    resource: str,
    action: Literal[
        "añadido",
        "añadida",
        "actualizado",
        "actualizada",
        "eliminado",
        "eliminada",
        "realizado",
        "realizada",
        "confirmado",
        "confirmada",
        "reenviado",
        "reenviada",
    ],
    status_code: int = 200,
) -> tuple[Response, int]:
    return (
        jsonify(msg=f"{resource.capitalize()} {action} de forma satisfactoria"),
        status_code,
    )


def to_json_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    return obj


def db_json_response(response: Union[list, dict]) -> tuple[Response, int]:
    return Response(json.dumps(response)), 200
