import random
import smtplib
import time
import uuid
import configparser

from email.message import EmailMessage

from flask import Flask, abort, redirect, url_for, render_template, request
from sqlitedict import SqliteDict

import db

app = Flask(__name__)


@app.route("/start/<uuid>/email", methods=["POST", "GET"])
def start(uuid):
    session = db.session(uuid)
    if session is None:
        abort(404)

    if request.method == "POST":
        email = request.form["email"]
        if not email.endswith("uwaterloo.ca"):
            # TODO: error feedback
            return redirect(url_for("start", uuid=uuid))

        sendmail_fake(email, session.verification_code, session.discord_name)
        return redirect(url_for("verify_get", uuid=uuid))

    else:
        return render_template("start.html")


@app.route("/verify/<uuid>", methods=["POST"])
def verify_post(uuid):
    # Post-Redirect-Get pattern
    attempted_code = request.form["verification"]
    verification_result = db.verify(uuid, attempted_code)

    if verification_result is True:
        return redirect(url_for("success"), code=303)
    elif verification_result == 0:
        # TODO: give 400 error? But who cares
        return redirect(url_for("failure"), code=303)
    else:
        return redirect(url_for("verify_get", uuid=uuid), code=303)


@app.route("/verify/<uuid>", methods=["GET"])
def verify_get(uuid):
    remaining_attempts = db.peek_attempts(uuid)

    if remaining_attempts is None:
        abort(404)

    assert (remaining_attempts > 0)

    return render_template(
        "verify.html",
        remaining_attempts=remaining_attempts,
    ), 200


@app.route("/success")
def success():
    return render_template("passed_verification.html")


@app.route("/failure")
def failure():
    return render_template("failed_verification.html")


def generate_message(email, code, name):
    msg = EmailMessage()
    body = (
        f"Your verification code is {code}",
        ""
        f"This email was triggered by {name}.",
    )
    msg.set_content("\n".join(body))
    msg['Subject'] = "Email Verification Code from AndrewBot"
    msg['From'] = "uw.andrew.bot@gmail.com"
    # TODO: Add a reply-to
    msg['To'] = str(email)
    return msg


def sendmail_fake(email, verif, name):
    msg = generate_message(email, verif, name)
    print(f"Sending fake email")
    print(msg)


def sendmail(email, verif, name):
    msg = generate_message(email, verif, name)

    # Send the message via our own SMTP server.
    # TODO: grab password from somewhere secure
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("LOGIN", "PASS")
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    app.run(debug=True)
