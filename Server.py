from flask import Flask,redirect,url_for,render_template,request
import uuid
import time
import random
import json
import uuid
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import configparser
from sqlitedict import SqliteDict


#for email sending
import smtplib
from email.message import EmailMessage


app = Flask(__name__)


@app.route("/<name>")
def home(name):
    return render_template("index.html",content=name)


@app.route("/new/<DID>")
def newuser(DID): #initialize new user
    uuid_user = uuid.uuid4()
    verifcode = (random.randint(10000000,99999999))
    with SqliteDict('./my_db.sqlite') as mydict:
            mydict[str(uuid_user)] = {
                "discordid": DID,
                "confirmationcode": verifcode,
                "verified": False,
                "failed_logins": 0}
            mydict.commit()
    return ("http://127.0.0.1:5000/verification/"+ str(uuid_user)+"/email")
  
    
@app.route("/verification/<UUID>/email",methods=["POST", "GET"])
def inputemail(UUID):
    if request.method == "POST":
        user = request.form["nm"]
        
        if user.endswith("uwaterloo.ca"): #sends email with verification code to user
            with SqliteDict('./my_db.sqlite') as mydict:
                verif_key = mydict[UUID]["confirmationcode"]
                sendmail(user,verif_key)
            initialize = 0
            return redirect(url_for("verifinput",UUID=UUID))
        
        else: #returns them to input email screen
            return redirect(url_for("inputemail",UUID=UUID))
            
    else:
        return render_template("login.html")
    
    

@app.route("/verifyinput/<UUID>",methods=["POST", "GET"])
def verifinput(UUID):
    if request.method == "POST":
        with SqliteDict('./my_db.sqlite') as mydict: #load up variables for further logic
            token = mydict[UUID]["confirmationcode"]
            verify_number = mydict[UUID]["failed_logins"]
        verification_form = request.form["verification"]
        
        if str(verification_form) == str(token): #if correctly inputs verification change them to verified
            print("debug1")
            with SqliteDict('./my_db.sqlite') as mydict:
                mydict[UUID]["verified"] = True
                mydict.commit()
            return redirect(url_for("verifworked"))
        
        elif verify_number == 5: #if 5 wrong inputs delete user
            with SqliteDict('./my_db.sqlite') as mydict:
                del mydict[UUID]
                mydict.commit()
            return redirect(url_for("veriffailed"))
            
        else: #if string is not matched add +1 to wrong verifyinput
            with SqliteDict('./my_db.sqlite') as mydict:
                variabledict = mydict[UUID]
                variabledict['failed_logins'] += 1
                mydict[UUID] = variabledict
                print("mydict", variabledict['failed_logins'])
                mydict.commit()
            return redirect(url_for("verifinput",UUID=UUID))
                    
    else:
        with SqliteDict('./my_db.sqlite') as mydict:
            attempts = mydict[UUID]['failed_logins']
        return render_template("verify.html",verify_number=attempts)

@app.route("/verifworked")
def verifworked():
    return render_template("passed_verification.html")

@app.route("/veriffailed")
def veriffailed():
    return render_template("failed_verification.html")



def sendmail(email,verif):
    msg = EmailMessage()
    msg.set_content('Hi, your verification code for the UW discord is: ' + str(verif))
    msg['Subject'] = 'University of Waterloo Verification Code'
    msg['From'] = "uw.andrew.bot@gmail.com"
    msg['To'] = str(email)

    # Send the message via our own SMTP server.
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("LOGIN", "PASS")
    server.send_message(msg)
    server.quit()   

if __name__ == "__main__":
    app.run(debug=True)