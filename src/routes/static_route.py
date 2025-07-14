from flask import Blueprint, send_from_directory, current_app

static_route = Blueprint("static", __name__)


@static_route.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(current_app.static_folder, filename)
