from flask import Flask

from .routes.auth_route import auth_route
from .routes.product_route import product_route
from .routes.revoked_token_route import token_revoked_route
from .routes.setting_route import setting_route
from .routes.user_route import user_route
from .services.auth_service import jwt, oauth
from .utils.db_utils import bcrypt, db

app = Flask(__name__)


def run_app(config):
    app.config.from_object(config)

    bcrypt.init_app(app)
    jwt.init_app(app)
    oauth.init_app(app)

    app.register_blueprint(user_route)
    app.register_blueprint(product_route)
    app.register_blueprint(setting_route)
    app.register_blueprint(auth_route)
    app.register_blueprint(token_revoked_route)

    return app
