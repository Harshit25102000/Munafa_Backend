import re
from flask import jsonify
from flask import session
from functools import wraps
import random
from mongo_connection import otp_db
from datetime import datetime, timedelta
import random
import string
def return_error(error="SOMETHING_WENT_WRONG", message="Error", data={}, code=200):
    return jsonify({"success": False, "error": error, "message": message, "data": data})


def return_success(data={}, status="SUCCESS", code=200):
    if isinstance(data, (dict, list)):
        if isinstance(data, (list)):
            l_data = {}
            l_data['status'] = status
            l_data['data'] = data
            return jsonify({"success": True, "data": l_data})
        if data.get('status', False):
            return jsonify({"success": True, "data": data})
        else:
            data['status'] = status
            return jsonify({"success": True, "data": data})
    else:
        raise Exception(f'data obj must be list or dict but got {type(data)}')



import re




def read_credentials_from_file(file_path):
    with open(file_path, 'r') as file:
        email = file.readline().strip()
        password = file.readline().strip()
    return email, password




def logged_in(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        email = session.get("email",None)
        if email:
            return f(*args, **kwargs)
        else:
            return return_error('LOGIN_REQUIRED',"Session not found login again")
    return decorated_func




def generate_otp():
    while True:
        # Generate a 4-digit random OTP
        otp = str(random.randint(1000, 9999))

        # Check if OTP already exists in the collection
        existing_otp = otp_db.find_one({'otp': otp})

        if not existing_otp:
            return otp

def shorten_to_25_words(text):
    words = text.split()
    return ' '.join(words[:20]) + ('...' if len(words) > 20 else '')

def shorten_to_10_words(text):
    words = text.split()
    return ' '.join(words[:10]) + ('...' if len(words) > 10 else '')

def generate_date_and_value_lists():
    # Generate a list of dates from the last 30 days
    today = datetime.now()
    date_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]

    # Generate a list of fluctuating values
    initial_value = 189
    value_list = [initial_value]
    for _ in range(29):  # 29 more values to match the length of date_list
        fluctuation = random.choice([-3, -2, -1, 1, 2, 3])  # Fluctuate by -3, -2, -1, 1, 2, or 3
        new_value = value_list[-1] + fluctuation
        value_list.append(new_value)

    return date_list, value_list