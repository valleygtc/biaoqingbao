from email.message import EmailMessage
from smtplib import SMTP_SSL

from .configs import configs


def send_email(to_addrs: str, subject: str, content: str) -> dict:
    """
    Params:
        to_addrs [str]: 多个则以英文逗号隔开
    Return:
        errors [dict]: {'<recepient>': (<error_code>, <error_msg>), ...}
    Exception:
        SMTPException: 这个是所有smtplib exception 的base exception class。
    """
    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = f"bqb-admin <{configs.EMAIL_USERNAME}>"
    email["To"] = to_addrs
    email.set_content(content)

    TIMEOUT = 2
    with SMTP_SSL(configs.EMAIL_HOST, timeout=TIMEOUT) as client:
        client.login(configs.EMAIL_USERNAME, configs.EMAIL_PASSWORD)
        errors = client.send_message(email)

    return errors
