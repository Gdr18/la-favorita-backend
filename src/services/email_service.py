from flask import Response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from config import SENDGRID_API_KEY, config, DEFAULT_SENDER_EMAIL
from ..utils.exceptions_management import handle_unexpected_error
from ..utils.successfully_responses import resource_msg


def send_email(token: str, user_info: dict) -> tuple[Response, int]:
    user_name = user_info.get("name")
    user_email = user_info.get("email")
    if config == "config.DevelopmentConfig":
        confirmation_link = f"http://localhost:5000/auth/confirm_email/{token}"
    else:
        # TODO: Cambiar la URL de producción
        confirmation_link = f"https://gador-auth.herokuapp.com/auth/confirm_email/{token}"

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
        print(response.body)
        print(response.headers)
        return resource_msg(user_name, "email de confirmación", "enviado", response.status_code)
    except Exception as e:
        return handle_unexpected_error(e)
