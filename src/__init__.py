from flask import Flask
from flask_jwt_extended import JWTManager

from .utils.db_utils import bcrypt

from .routes.user_route import user_route
from .routes.product_route import product_route
from .routes.auth_route import auth

app = Flask(__name__)

jwt = JWTManager()


def run_app(config):
    app.config.from_object(config)

    bcrypt.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(user_route)
    app.register_blueprint(product_route)
    app.register_blueprint(auth)

    return app
