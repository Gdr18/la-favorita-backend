import pytest
from flask import Flask
from src.app import run_app
from src.services.security_service import jwt, oauth, bcrypt


@pytest.fixture()
def app():
    config = {}
    return run_app(config)


def test_app_creation(app):
    assert isinstance(app, Flask)


def test_blueprints_registration(app):
    expected_blueprints = [
        "users",
        "products",
        "settings",
        "auth",
        "revoked_tokens",
        "refresh_tokens",
        "email_tokens",
        "orders",
        "dishes",
    ]
    assert all(bp in app.blueprints for bp in expected_blueprints)


def test_security_services_initialization(mocker):
    mocker.patch.object(bcrypt, "init_app")
    mocker.patch.object(jwt, "init_app")
    mocker.patch.object(oauth, "init_app")

    config = {}
    another_app = run_app(config)

    bcrypt.init_app.assert_called_once_with(another_app)
    jwt.init_app.assert_called_once_with(another_app)
    oauth.init_app.assert_called_once_with(another_app)
