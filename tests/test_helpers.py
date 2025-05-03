import pytest

from flask_jwt_extended import create_access_token, create_refresh_token
from src.app import run_app
from config import config


@pytest.fixture
def app():
    app = run_app(config)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(app):
    with app.app_context():
        access_token = create_access_token(identity="507f1f77bcf86cd799439011", additional_claims={"role": 0}, fresh=True)
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_header_refresh(app):
    with app.app_context():
        refresh_token = create_refresh_token(identity="507f1f77bcf86cd799439011", additional_claims={"role": 1})
        return {"Authorization": f"Bearer {refresh_token}"}
