import smtplib
from email.message import EmailMessage


def _generate_message(email, code, name):
    msg = EmailMessage()
    body = (
        f"Your verification code is {code}",
        ""
        f"This email was triggered by {name}.",
    )
    msg.set_content("\n".join(body))
    msg['Subject'] = "Email Verification Code from AndrewBot"
    msg['From'] = "uw.andrew.bot@gmail.com"
    msg['To'] = str(email)
    return msg


class SMTPMailer(object):
    """A Mailer sends out emails."""
    __slots__ = ["host", "port", "username", "password"]

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def send(self, address, code, name):
        msg = _generate_message(address, code, name)
        server = smtplib.SMTP_SSL(self.host, self.port)
        server.login(self.username, self.password)
        server.send_message(msg)
        server.quit()


class PrintMailer(object):
    """A mailer that just prints things instead of sending for real."""
    __slots__ = []

    def send(self, address, code, name):
        msg = _generate_message(address, code, name)
        print("Email to send")
        print(msg)
