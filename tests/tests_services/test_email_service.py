import pytest
from unittest.mock import MagicMock, patch, mock_open
from sendgrid import Mail
from flask import Response

from src.services.email_service import send_email
from src.app import run_app
from config import config


USER_INFO = {"name": "Test User", "email": "test@example.com", "_id": "60d21b4667d0d8992e610c85"}


@pytest.fixture
def app():
    app = run_app(config)
    app.config["TESTING"] = True
    return app


def test_send_email(app, mocker):
    with app.app_context():
        token_email = "mocked_token"
        confirmation_link = f"http://localhost:5000/auth/confirm-email/{token_email}"
        email_template = "<html><body>Confirm your email: <a href='{{ confirmation_link }}'>here</a></body></html>"

        mocker.patch("src.services.security_service.create_access_token", return_value="mocked_token")

        mocker.patch("src.services.security_service.decode_token", return_value={
            "sub": "60d21b4667d0d8992e610c85",
            "jti": "mocked_jti",
            "exp": 1723934650
        })

        mocked_token_model = MagicMock()
        mocker.patch("src.services.security_service.TokenModel", return_value=mocked_token_model)
        mocked_token_model.insert_email_token.return_value = None

        mock_open = mocker.mock_open(read_data=email_template)
        mocker.patch("builtins.open", mock_open)

        mock_sendgrid_client = mocker.patch("src.services.email_service.SendGridAPIClient", autospec=True)
        mock_instance = mock_sendgrid_client.return_value
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 202
        mock_instance.send = MagicMock(return_value=mock_response)

        response = send_email(USER_INFO)

        mock_instance.send.assert_called_once()
        sent_email = mock_instance.send.call_args[0][0]
        assert isinstance(sent_email, Mail)
        assert sent_email.from_email.email == "gador8@gmail.com"
        assert sent_email.personalizations[0].tos[0].get("email") == USER_INFO["email"]
        assert sent_email.subject.subject == "Confirma el email de registro"
        assert confirmation_link in sent_email.contents[0].content
        assert response.status_code == 202


def test_send_email_confirmation_link_production(mocker):
    mocker.patch("src.services.email_service.config", "config.ProductionConfig")
    mocker.patch("src.services.email_service.generate_email_token", return_value="mocked_token")
    mock_sendgrid_client = mocker.patch("src.services.email_service.SendGridAPIClient", autospec=True)

    send_email(USER_INFO)

    confirmation_link = "https://gador-auth.herokuapp.com/auth/confirm-email/mocked_token"
    mock_sendgrid_client.assert_called_once()
    sent_email = mock_sendgrid_client.return_value.send.call_args[0][0]
    assert confirmation_link in sent_email.contents[0].content
