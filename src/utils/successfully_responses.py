from flask import jsonify, Response


def resource_msg(resource_id: str, resource, action, status_code=200) -> tuple[Response, int]:
    return (
        jsonify(msg=f"{resource.capitalize()} '{resource_id}' ha sido {action} de forma satisfactoria"),
        status_code,
    )


def db_json_response(response) -> tuple[Response, int]:
    return jsonify(response), 200
