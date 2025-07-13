import pytest
from sendgrid import Mail
from flask import Response

from src.services.email_service import send_email
from tests.test_helpers import app

USER_INFO = {
    "name": "Test User",
    "email": "test@example.com",
    "_id": "60d21b4667d0d8992e610c85",
}


def test_send_email(app, mocker):
    with app.app_context():
        token_email = "mocked_token"
        confirmation_link = f"http://localhost:5000/auth/confirm-email/{token_email}"
        email_template = "<html><body>Confirm your email: <a href='{{ confirmation_link }}'>here</a></body></html>"

        mock_generate_email_token = mocker.patch(
            "src.services.email_service.generate_email_token",
            return_value="mocked_token",
        )

        mock_open = mocker.mock_open(read_data=email_template)
        mock_open_patch = mocker.patch("builtins.open", mock_open)

        mock_sendgrid_client = mocker.patch(
            "src.services.email_service.SendGridAPIClient", autospec=True
        )
        mock_instance = mock_sendgrid_client.return_value
        mock_response = mocker.MagicMock(spec=Response)
        mock_response.status_code = 202
        mock_instance.send = mocker.MagicMock(return_value=mock_response)

        response = send_email(USER_INFO)

        sent_email = mock_instance.send.call_args[0][0]
        assert isinstance(sent_email, Mail)
        assert sent_email.personalizations[0].tos[0].get("email") == USER_INFO["email"]
        assert sent_email.subject.subject == "Confirma el email de registro"
        assert confirmation_link in sent_email.contents[0].content
        assert response.status_code == 202
        mock_generate_email_token.assert_called_once_with(USER_INFO)
        mock_sendgrid_client.assert_called_once()
        mock_open_patch.assert_called_once()
