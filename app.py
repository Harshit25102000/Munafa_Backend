from flask_cors import CORS, cross_origin
import json
from common_functions import *
from flask import Flask, render_template_string, request, session, redirect, url_for,send_file, Response
from mongo_connection import *
from flask_session import Session
import bcrypt
import csv
import io
import requests

from flask_bcrypt import Bcrypt
app = Flask(__name__)
app.secret_key = "harshit25102000"
CORS(app,supports_credentials=True)
# import random
import time
# import pytz
# from io import BytesIO
# import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



# Configuration
file_path = 'credentials.txt'
EMAIL_ADDRESS, EMAIL_PASSWORD = read_credentials_from_file(file_path)



@app.route("/send_signup_otp",methods=["POST"])
def send_signup_otp():
    try:
        print(request)
        data = request.get_json()
        email = data["email"]

        otp=generate_otp()
        otp_db.insert_one({"otp":otp})
        # sending mail----------------------------
        subject = "Munafa OTP for Sign Up"
        body = f"Your OTP for Munafa Signup Process is\n{otp}\nIf this was not you then please contact us at :\nharshit25102000@gmail.com"

        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(email, email, msg.as_string())
        return return_success()
    except Exception as e:
         return return_error(message=str(e))

@app.route("/verify_signup_otp",methods=["POST"])
def verify_signup_otp():
    try:

        data = request.get_json()
        email = data["email"]
        otp = data["otp"]
        if not isinstance(otp,str):
            return return_error(error="OTP_MUST_BE_STRING", message="OTP must be a string datatype")
        value=otp_db.find_one({"otp":otp})
        if value is None:
            return return_error(error="INVALID_OTP", message="No such otp exists in the database")
        otp_db.delete_one({"otp":otp})
        verified_emails.insert_one({"email":email})
        return return_success()
    except Exception as e:
         return return_error(message=str(e))
@app.route("/signup",methods=["POST"])
def signup():
    try:

        data = request.get_json()
        name = data["name"]
        email = data["email"]
        password = data["password1"]
        password2=data["password2"]
        login_user = user_credentials.find_one({'email': email})
        if login_user is not None:

            return return_error(error="ACCOUNT_ALREADY_EXIST", message="Account already exists")
        verify=verified_emails.find_one({'email': email})
        if verify is None:
            return return_error(error="EMAIL_NOT_VERIFIED", message="Email not verified with OTP")
        if not password==password2:

            return return_error(error="PASSWORDS_DON'T_MATCH", message="Passwords do not match")
        # converting password to array of bytes

        bytes = password.encode('utf-8')

        # generating the salt
        salt = bcrypt.gensalt()
        hashpass=bcrypt.hashpw(bytes, salt)
        query={"name":name, "password":hashpass,"email":email}
        user_credentials.insert_one(query)
        session["email"]=email
        verified_emails.delete_one({"email":email})
        return return_success({"email":email})
    except Exception as e:
         return return_error(message=str(e))


@app.route("/login",methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data["email"]

        password = data["password"]


        login_user=user_credentials.find_one({'email':email})

        if login_user is None:

            return return_error(error="ACCOUNT_DOES_NOT_EXIST", message="No account exists with this email address")
        # converting password to array of bytes
        given_password=password.encode('utf-8')
        result=bcrypt.checkpw(given_password, login_user["password"])

        if not result:
            return return_error(error="WRONG_PASSWORD", message="Wrong password for this email")



        session["email"]=email
        return return_success({"email":session["email"]})
    except Exception as e:
        return return_error(message=str(e))

@app.route("/logout",methods=["GET"])
@logged_in
def logout():
    try:
        del session["email"]
        return return_success(status="LOGOUT")
    except Exception as e:
        return return_error(message=str(e))

@app.route("/@me",methods=["GET"])
@logged_in
def at_me():
    user_id = session.get("email")
    if not user_id:
        return return_error(error="UNAUTHORIZED",code=401)
    else:
        return return_success(data={"email": user_id})

@app.route("/get_data",methods=["GET"])
def get_data():
    try:
        symbol="IBM"
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'
        r = requests.get(url)
        data = r.json()
        print(data)
        symb=data['Symbol']
        exchange=data["Exchange"]
    
        return return_success(data={"symbol": symb,"exchange":exchange})
        
    except Exception as e:
        return return_error(message=str(e))


@app.route("/get_index_data",methods=["GET"])
def get_index_data():
    
        symbols=["GOOG","AMZN","JPM","F","AAPL"]
        res=[]
        negative=False
        for symbol in symbols:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'
            r = requests.get(url)
            data = r.json()
            print(data)
            quote=data["Global Quote"]
            print(quote)
            print(type(quote))
            change_percent=quote["10. change percent"]
            price=quote["05. price"]
            
            dict={}
            dict["change_percent"]=change_percent[:-1]
            
            if change_percent.startswith('-'):
                negative=True
            dict["price"]=price
            dict["symbol"]=symbol
            dict["negative"]=negative
            
            res.append(dict)

            
    
        return return_success(res)
        


@app.route("/get_chart_data",methods=["POST"])
def get_chart_data():
    try:
        data = request.get_json()

        symbol = data["symbol"]

        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'
        
        r = requests.get(url)
        data = r.json()
        
      
        date=[]
        close=[]
        temp=data['Time Series (Daily)']
        for i in temp:
            print(i)
            print(temp[i]['4. close'])
            date.append(i)
            close.append(temp[i]["4. close"])
        print(date,close)
       
    
        return return_success(data={"date": date,"close":close})
        
    except Exception as e:
        return return_error(message=str(e))


@app.route("/get_all_price", methods=["GET"])
def get_all_price():
    try:
        symbols = ["ibm","msft","tsla","race"]
        result=[]
        for symbol in symbols:
            # time.sleep(3)
            # url = f"https://echios.tech/price/{symbol}?apikey=GRP14XN3TW0RK"
            # r = requests.get(url)
            # print(r)
            # data = r.json()
            # price=data["price"]
            price=100
            bid = round(price - 0.5, 2)
            ask = price + 1
            dic={"price": price, "bid": bid, "ask":ask,"symbol":symbol}
            print(dic)
            result.append(dic)
            # time.sleep(3)




        return return_success(result)

    except Exception as e:
        return return_error(message=str(e))



@app.route("/execute_trade",methods=["POST"])
def execute_trade():
    try:
        data = request.get_json()
        print(data)
        qty=data["qty"]
        action=data["action"]
        bid=data["bid"]
        ask=["ask"]
        symbol=data["symbol"]
        query={"qty":qty,"action":action,"bid":bid,"ask":ask,"symbol":symbol,"email":session["email"]}
        # transactions.insert_one(query)


       
       
        return return_success(query)
    except Exception as e:
        return return_error(message=str(e))

if __name__=="__main__":

    app.config['DEBUG'] = True
    app.secret_key = "harshit25102000"
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    app.config["SESSION_PERMANENT"] = True
    app.config["SESSION_TYPE"] = "mongodb"
    app.config["SESSION_MONGODB"] = client
    app.config["SESSION_MONGODB_DB"] = 'userData'
    app.config["SESSION_MONGODB_COLLECTION"] = 'sessions'
    Session(app)
    app.run(debug=True)


