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

#Configurations
config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['MAIN']['API']

app = Flask(__name__)


@app.route("/<name>")
def home(name):
    return render_template("index.html",content=name)


@app.route("/new/<DID>")
def newuser(DID): #initialize new user
    uuid_user = uuid.uuid4()
    verifcode = (random.randint(10000000,99999999))
    with open('data.txt' ,'r') as json_file:
            data = json.load(json_file)
    with open('data.txt' , 'w') as json_file:
            data[str(uuid_user)] = {
                "discordid": DID,
                "confirmationcode": verifcode,
                "verified": False,
                "failed_logins": 0}
            json_file.write(json.dumps(data))
    return ("http://127.0.0.1:5000/verification/"+ str(uuid_user)+"/email")
  
    
@app.route("/verification/<UUID>/email",methods=["POST", "GET"])
def inputemail(UUID):
    if request.method == "POST":
        user = request.form["nm"]
        
        if "@uwaterloo.ca" in user: #sends email with verification code to user
            with open('data.txt' ,'r') as json_file:
                data = json.load(json_file)
                verif_key = data[UUID]["confirmationcode"]
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
        with open ('data.txt','r') as json_file: #load up variables for further logic
            data = json.load(json_file)
            token = data[UUID]["confirmationcode"]
            verify_number = data[UUID]["failed_logins"]
        verification_form = request.form["verification"]
        
        if str(verification_form) == str(token): #if correctly inputs verification change them to verified
            print("debug1")
            with open ('data.txt','r') as json_file:
                data = json.load(json_file)
                data[UUID]["verified"] = True
            with open ('data.txt','w') as json_file:
                json.dump(data,json_file)
            return redirect(url_for("verifworked"))
        
        elif verify_number == 5: #if 5 wrong inputs delete user
            with open ('data.txt','r') as json_file:
                data = json.load(json_file)
                del data[UUID]
            with open ('data.txt','w') as json_file:
                json.dump(data,json_file)
            return redirect(url_for("veriffailed"))
            
        else: #if string is not matched add +1 to wrong verifyinput
            with open ('data.txt','r+') as json_file:
                data = json.load(json_file)
                data[UUID]["failed_logins"] = (verify_number + 1)
            with open ('data.txt','w') as json_file:
                json.dump(data,json_file)
            return redirect(url_for("verifinput",UUID=UUID))
                    
    else:
        with open ('data.txt','r') as json_file:
            data = json.load(json_file)
            attempts = data[UUID]['failed_logins']
        return render_template("verify.html",verify_number=attempts)

@app.route("/verifworked")
def verifworked():
    return render_template("passed_verification.html")

@app.route("/veriffailed")
def veriffailed():
    return render_template("failed_verification.html")



def sendmail(email,verif):
    message = Mail(
        from_email='uw.andrew.bot@gmail.com',
        to_emails=str(email),
        subject='Sending with Twilio SendGrid is Fun',
        html_content=('<strong>Your verification key is:</strong>'+str(verif)))
    sg = SendGridAPIClient(str(API_KEY))
    response = sg.send(message)

if __name__ == "__main__":
    app.run(debug=True)