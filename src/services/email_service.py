from flask import Response
from flask_jwt_extended import decode_token
from sendgrid import SendGridAPIClient, Mail

from config import config, SENDGRID_API_KEY, DEFAULT_SENDER_EMAIL
from ..models.token_model import TokenModel
from ..services.auth_service import generate_email_token
from ..utils.exceptions_management import handle_unexpected_error
from ..utils.successfully_responses import resource_msg


def send_email(user_info: dict) -> tuple[Response, int]:
    token_email = generate_email_token(user_info)
    decoded_token_email = decode_token(token_email)
    data_email_token_db = {
        "user_id": decoded_token_email.get("sub"),
        "jti": decoded_token_email.get("jti"),
        "expires_at": decoded_token_email.get("exp"),
    }
    try:
        inserted_email_token = TokenModel(**data_email_token_db).insert_email_token()
        if inserted_email_token:
            user_name = user_info.get("name")
            user_email = user_info.get("email")
            if config == "config.DevelopmentConfig":
                confirmation_link = f"http://localhost:5000/auth/confirm_email/{token_email}"
            else:
                # TODO: Cambiar la URL de producción
                confirmation_link = f"https://gador-auth.herokuapp.com/auth/confirm_email/{token_email}"
            with open("src/utils/email_template.html", encoding="utf-8") as file:
                email_template = file.read()
                email_template = email_template.replace("{{ confirmation_link }}", confirmation_link).replace(
                    "{{ user_name }}", user_name
                )
            mail = Mail(
                from_email=DEFAULT_SENDER_EMAIL,
                to_emails=user_email,
                subject="Confirma el email de registro",
                html_content=email_template,
            )
            try:
                sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
                response = sg.send(mail)
                print(response.status_code)
                print(token_email)
                return resource_msg(user_name, "email de confirmación", "enviado", response.status_code)
            except Exception as e:
                return handle_unexpected_error(e)
        raise Exception("Error al insertar el email token")
    except Exception as e:
        return handle_unexpected_error(e)
