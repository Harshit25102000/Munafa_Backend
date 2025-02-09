from flask_cors import CORS, cross_origin
import json
from common_functions import *
from flask import Flask, render_template_string, request, session, redirect, url_for, send_file, Response
from mongo_connection import *
from flask_session import Session
import bcrypt
import csv
import io
import requests

from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "harshit25102000"
CORS(app, supports_credentials=True)
# import random
from datetime import datetime
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


@app.route("/send_signup_otp", methods=["POST"])
def send_signup_otp():
    try:
        print(request)
        data = request.get_json()
        email = data["email"]

        otp = generate_otp()
        otp_db.insert_one({"otp": otp})
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


@app.route("/verify_signup_otp", methods=["POST"])
def verify_signup_otp():
    try:

        data = request.get_json()
        email = data["email"]
        otp = data["otp"]
        if not isinstance(otp, str):
            return return_error(error="OTP_MUST_BE_STRING", message="OTP must be a string datatype")
        value = otp_db.find_one({"otp": otp})
        if value is None:
            return return_error(error="INVALID_OTP", message="No such otp exists in the database")
        otp_db.delete_one({"otp": otp})
        verified_emails.insert_one({"email": email})
        return return_success()
    except Exception as e:
        return return_error(message=str(e))


@app.route("/signup", methods=["POST"])
def signup():
    try:

        data = request.get_json()
        name = data["name"]
        email = data["email"]
        password = data["password1"]
        password2 = data["password2"]
        login_user = user_credentials.find_one({'email': email})
        if login_user is not None:
            return return_error(error="ACCOUNT_ALREADY_EXIST", message="Account already exists")
        verify = verified_emails.find_one({'email': email})
        if verify is None:
            return return_error(error="EMAIL_NOT_VERIFIED", message="Email not verified with OTP")
        if not password == password2:
            return return_error(error="PASSWORDS_DON'T_MATCH", message="Passwords do not match")
        # converting password to array of bytes

        bytes = password.encode('utf-8')

        # generating the salt
        salt = bcrypt.gensalt()
        hashpass = bcrypt.hashpw(bytes, salt)
        query = {"name": name, "password": hashpass, "email": email}
        user_credentials.insert_one(query)
        session["email"] = email
        verified_emails.delete_one({"email": email})
        return return_success({"email": email})
    except Exception as e:
        return return_error(message=str(e))


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data["email"]

        password = data["password"]

        login_user = user_credentials.find_one({'email': email})

        if login_user is None:
            return return_error(error="ACCOUNT_DOES_NOT_EXIST", message="No account exists with this email address")
        # converting password to array of bytes
        given_password = password.encode('utf-8')
        result = bcrypt.checkpw(given_password, login_user["password"])

        if not result:
            return return_error(error="WRONG_PASSWORD", message="Wrong password for this email")

        session["email"] = email
        return return_success({"email": session["email"]})
    except Exception as e:
        return return_error(message=str(e))


@app.route("/logout", methods=["GET"])
@logged_in
def logout():
    try:
        del session["email"]
        return return_success(status="LOGOUT")
    except Exception as e:
        return return_error(message=str(e))


@app.route("/@me", methods=["GET"])
@logged_in
def at_me():
    user_id = session.get("email")
    if not user_id:
        return return_error(error="UNAUTHORIZED", code=401)
    else:
        return return_success(data={"email": user_id})


@app.route("/get_data", methods=["GET"])
def get_data():
    try:
        symbol = "IBM"
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'
        r = requests.get(url)
        data = r.json()
        print(data)
        symb = data['Symbol']
        exchange = data["Exchange"]

        return return_success(data={"symbol": symb, "exchange": exchange})

    except Exception as e:
        return return_error(message=str(e))


@app.route("/get_index_data", methods=["GET"])
def get_index_data():
    symbols = ["GOOG", "AMZN", "JPM", "F", "AAPL"]
    res = []
    negative = False
    for symbol in symbols:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'
        r = requests.get(url)
        data = r.json()
        print(data)
        quote = data["Global Quote"]
        print(quote)
        print(type(quote))
        change_percent = quote["10. change percent"]
        price = quote["05. price"]

        dict = {}
        dict["change_percent"] = change_percent[:-1]

        if change_percent.startswith('-'):
            negative = True
        dict["price"] = price
        dict["symbol"] = symbol
        dict["negative"] = negative

        res.append(dict)

    return return_success(res)


@app.route("/get_chart_data", methods=["POST"])
def get_chart_data():
    try:
        data = request.get_json()

        symbol = data["symbol"]
        try:
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'
            print(url)
            r = requests.get(url)
            data = r.json()
            print(data)

            date = []
            close = []
            temp = data['Time Series (Daily)']
            for i in temp:
                print(i)
                print(temp[i]['4. close'])
                date.append(i)
                close.append(temp[i]["4. close"])

        except:
            date, close = generate_date_and_value_lists()

        return return_success(data={"date": date, "close": close})

    except Exception as e:
        return return_error(message=str(e))


@app.route("/get_all_price", methods=["GET"])
def get_all_price():
    time.sleep(5)
    try:
        symbols = ["ibm", "msft", "tsla", "race"]
        result = []
        for symbol in symbols:
            time.sleep(3)
            url = f"https://echios.tech/price/{symbol}?apikey=GRP14XN3TW0RK"
            r = requests.get(url)
            print(r)
            data = r.json()
            price = data["price"]
            bid = round(price - 0.5, 2)
            ask = price + 1
            dic = {"price": price, "bid": bid, "ask": ask, "symbol": symbol}
            print(dic)
            result.append(dic)
            # time.sleep(3)

        return return_success(result)

    except Exception as e:
        return return_error(message=str(e))


@app.route("/execute_trade", methods=["POST"])
@logged_in
def execute_trade():
    try:
        data = request.get_json()
        print(data)
        qty = data["qty"]
        qty = float(qty)
        action = data["action"]
        bid = data["bid"]
        ask = data["ask"]
        print(bid, ask, qty)
        bid = float(bid)
        ask = float(ask)
        symbol = data["symbol"]
        sl = data["stopLoss"]
        limit = data["limitPrice"]

        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        query = {"qty": qty, "action": action, "bid": bid, "ask": ask, "symbol": symbol, "email": session["email"],
                 "date": current_date, "time": current_time}
        transactions.insert_one(query)
        if action == "buy":
            x = portfolio.find_one({"symbol": symbol})
            if x:
                my_query = {"symbol": symbol}
                new_qty = x["qty"] + qty
                new_invested_amount = x["invested"] + bid * qty
                updated_vals = {"$set": {"qty": new_qty, "invested": new_invested_amount}}
                portfolio.update_one(my_query, updated_vals)
            else:
                portfolio.insert_one({"qty": qty, "symbol": symbol, "email": session["email"], "invested": bid * qty})
        elif action == "sell":
            x = portfolio.find_one({"symbol": symbol})
            if x:

                if qty > x["qty"]:
                    return return_error(error="Insufficient stocks")
                else:

                    my_query = {"symbol": symbol}
                    new_qty = x["qty"] - qty
                    new_invested_amount = x["invested"] - ask * qty
                    updated_vals = {"$set": {"qty": new_qty, "invested": new_invested_amount}}
                    portfolio.update_one(my_query, updated_vals)

            else:
                return return_error(error="Stock Not Found")

        if sl != "":
            stop_loss.insert_one({"qty": qty, "symbol": symbol, "stop_loss": sl, "email": session["email"]})

        return return_success()
    except Exception as e:
        print(e)
        return return_error(message=str(e))


@app.route("/get_portfolio", methods=["GET"])
@logged_in
def get_portfolio():
    time.sleep(5)
    try:
        email = session["email"]
        x = portfolio.find({"email": email})
        shares = []
        total_invested = 0

        symbols = ["ibm", "msft", "tsla", "race"]
        price_result = {}
        for symbol in symbols:
            time.sleep(3)
            url = f"https://echios.tech/price/{symbol}?apikey=GRP14XN3TW0RK"
            r = requests.get(url)
            print(r)
            data = r.json()
            price = data["price"]
            price = float(price)
            price_result[symbol] = price
            print(price_result)

        for i in x:
            dict = {}
            dict["qty"] = i["qty"]
            dict["symbol"] = i["symbol"]
            dict["invested"] = i['invested']
            dict["price"] = price_result[i['symbol']]
            dict["current_value"] = round(price_result[i['symbol']] * i['qty'], 2)
            shares.append(dict)
            total_invested = total_invested + i['invested']

        current_val = 0
        for share in shares:
            current_val = current_val + share['price'] * share['qty']
        returns = ((current_val - total_invested) / total_invested) * 100
        returns = round(returns, 2)

        result = {'shares': shares, 'total_invested': total_invested, 'current_val': round(current_val, 2),
                  'returns': returns}
        return return_success(result)
    except Exception as e:
        print(e)
        return return_error(message=str(e))


@app.route("/get_transactions", methods=["GET"])
@logged_in
def get_transactions():
    time.sleep(5)
    try:
        x = transactions.find({"email": session["email"]})
        result = []
        for i in x:
            dict = {}
            dict['qty'] = i['qty']
            dict['action'] = i['action']
            if i['action'] == 'buy':
                dict['amount'] = i['bid'] * i['qty']
                dict['rate'] = i['bid']
            else:
                dict['amount'] = i['ask'] * i['qty']
                dict['rate'] = i['ask']
            dict['symbol'] = i['symbol']
            dict['date'] = i['date']
            dict['time'] = i['time']
            result.append(dict)

        return return_success(result)
    except Exception as e:
        print(e)
        return return_error(message=str(e))


@app.route("/get_news", methods=["GET"])
def get_news():
    try:

        url = f'https://newsapi.org/v2/everything?q=stocks&apiKey=aff915ce85ae4475ac01ff6df1bfed46'
        res = []
        r = requests.get(url)
        data = r.json()

        articles = data['articles']
        counter = 0
        for article in articles:

            dict = {}
            dict['heading'] = article['title']

            dict['paragraph'] = article['description']
            dict['link'] = article['url']
            if dict['heading'] is not None and dict['paragraph'] is not None and dict['link'] is not None:
                dict['paragraph'] = shorten_to_25_words(dict['paragraph'])
                dict['heading'] = shorten_to_10_words(dict['paragraph'])
                res.append(dict)
                counter = counter + 1
            if counter > 20:
                break
        return return_success(res)

    except Exception as e:
        return return_error(message=str(e))

@app.route("/get_fundamentals", methods=["POST"])
def get_fundamentals():
    try:
        try:
            data = request.get_json()

            symbol = data["symbol"]
            url=f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey=THXW5Z2G9JZKTRK4'



            r = requests.get(url)
            data = r.json()
            res={"description":data['Description'],"TwoHundredDayMovingAvg":data['200DayMovingAverage'],"FityDayMovingAvg":data['50DayMovingAverage'],"peratio":data['PERatio'],
                 "ebitda": data['EBITDA'], "market_cap": data['MarketCapitalization'],
                 "fifty_two_week_low": data['52WeekLow'], "fifty_two_week_high": data['52WeekHigh']
                 }
        except:
            with open('desc.txt', 'r') as file:
                desc = file.read()
            res = {"description": desc, "TwoHundredDayMovingAvg": "171.76",
                    "FityDayMovingAvg": "175.88", "peratio": '21.18',
                    "ebitda": '1462500000', "market_cap": '176989389000',
                    "fifty_two_week_low": '131.82', "fifty_two_week_high": '197.22'}



        return return_success(data=res)


    except Exception as e:

        return return_error(message=str(e))

if __name__ == "__main__":
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


