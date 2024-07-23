import pymongo

# client = pymongo.MongoClient("mongodb://localhost:27017/")

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import urllib
uri = "mongodb+srv://harshit25102000:"+urllib.parse.quote("Harshit@#25102000")+"@cluster0.5yxzpvw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
print(client)
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client['Munafa']
user_credentials = db['user_credentials']
otp_db = db['otp_db']
verified_emails=db['verified_emails']
