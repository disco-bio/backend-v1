from pymongo import MongoClient
from dotenv import load_dotenv
from pprint import pprint
import datetime
import os


load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

mongo_client = MongoClient(MONGODB_URI)

testDatabase = mongo_client.testDatabase
testCollection = testDatabase.testCollection

sample_item = {
	"data": "Hello world!",
	"datetimeCreated": datetime.datetime.utcnow(),
	"datetimeModified": datetime.datetime.utcnow()
}

pprint(sample_item)

# pprint("sample item:", sample_item)

testCollection.insert_one(sample_item)

for item in testCollection.find():
	pprint(item)

