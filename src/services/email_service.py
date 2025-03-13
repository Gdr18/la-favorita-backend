from sendgrid import SendGridAPIClient, Mail
from flask import Response

from config import config, SENDGRID_API_KEY, DEFAULT_SENDER_EMAIL
from src.services.security_service import generate_email_token


def send_email(user_info: dict) -> Response:
    token_email = generate_email_token(user_info)
    user_name = user_info.get("name")
    user_email = user_info.get("email")
    if config == "config.DevelopmentConfig":
        confirmation_link = f"http://localhost:5000/auth/confirm-email/{token_email}"
    else:
        # TODO: Cambiar la URL de producción
        confirmation_link = f"https://gador-auth.herokuapp.com/auth/confirm-email/{token_email}"
    with open("src/templates/email_template.html", encoding="utf-8") as file:
        email_template = file.read()
        email_template = email_template.replace("{{ confirmation_link }}", confirmation_link).replace(
            "{{ user_name }}", user_name
        )
    email = Mail(
        from_email=DEFAULT_SENDER_EMAIL,
        to_emails=user_email,
        subject="Confirma el email de registro",
        html_content=email_template,
    )

    sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = sg.send(email)
    return response
