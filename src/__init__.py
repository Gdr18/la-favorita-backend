from flask import Flask

from .utils.db import bcrypt
from .routes.users import user
from .routes.roles import role

app = Flask(__name__)


def run_app(config):
    app.config.from_object(config)

    bcrypt.init_app(app)

    app.register_blueprint(user)
    app.register_blueprint(role)
    return app
