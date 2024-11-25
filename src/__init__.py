from authlib.integrations.flask_client import (
    OAuth,
)
from flask import (
    Flask,
)

from .routes.auth_route import (
    auth_route,
)
from .routes.product_route import (
    product_route,
)
from .routes.revoked_token_route import (
    token_revoked_route,
)
from .routes.setting_route import (
    setting_route,
)
from .routes.user_route import (
    user_route,
)
from .utils.db_utils import (
    bcrypt,
    db,
    jwt,
)

app = Flask(
    __name__
)
oauth = OAuth(app)


def run_app(config):
    app.config.from_object(
        config
    )

    google = oauth.register(
        name="google",
        client_id=app.config[
            "CLIENT_ID"
        ],
        client_secret=app.config[
            "CLIENT_SECRET"
        ],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        },
    )

    bcrypt.init_app(
        app
    )
    jwt.init_app(
        app
    )
    oauth.init_app(
        app
    )

    app.register_blueprint(
        user_route
    )
    app.register_blueprint(
        product_route
    )
    app.register_blueprint(
        setting_route
    )
    app.register_blueprint(
        auth_route
    )
    app.register_blueprint(
        token_revoked_route
    )

    return app
