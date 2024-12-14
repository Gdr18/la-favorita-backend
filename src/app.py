from flask import Flask

from src.routes.auth_route import auth_route
from src.routes.email_token_route import email_token_route
from src.routes.product_route import product_route
from src.routes.refresh_token_route import refresh_token_route
from src.routes.revoked_token_route import token_revoked_route
from src.routes.setting_route import setting_route
from src.routes.user_route import user_route
from src.services.security_service import jwt, oauth, bcrypt

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
    app.register_blueprint(refresh_token_route)
    app.register_blueprint(email_token_route)

    return app
