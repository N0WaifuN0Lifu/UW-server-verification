import os
import random
import time
import uuid
import configparser

from flask import Flask, abort, redirect, url_for, render_template, request
from sqlitedict import SqliteDict

import db
import mailer

app = Flask(__name__)
smtp_host = os.environ.get("ANDREWBOT_SMTP_HOST", None)
smtp_port = os.environ.get("ANDREWBOT_SMTP_PORT", 465)
smtp_user = os.environ.get("ANDREWBOT_SMTP_USER", None)
smtp_pass = os.environ.get("ANDREWBOT_SMTP_PASS", None)
smtp_from_addr = os.environ.get("ANDREWBOT_SMTP_FROM", None)
if smtp_host is None:
    mail = mailer.PrintMailer()
else:
    mail = mailer.SMTPMailer(
        host=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_pass,
        from_addr=smtp_from_addr
    )


@app.route("/start/<uuid>/email", methods=["POST", "GET"])
def start(uuid):
    session = db.session(uuid)
    if session is None:
        abort(404)

    # If the user has entered an email ready, take them to the code
    # verification form.
    if session.state == db.SessionState.WAITING_ON_CODE:
        return redirect(url_for("verify_get", uuid=uuid), code=303)

    if request.method == "POST":
        email = request.form["email"]
        if not email.endswith("uwaterloo.ca"):
            # TODO: error feedback
            return redirect(url_for("start", uuid=uuid), code=303)

        mail.send(email, session.verification_code, session.discord_name)
        db.set_email_sent(uuid)
        return redirect(url_for("verify_get", uuid=uuid), code=303)

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

@app.route("/")
def root():
    return render_template("index.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    session_id = db._new_fake_session()
    print(f"http://localhost:5000/start/{session_id}/email")
    app.run(debug=True)
