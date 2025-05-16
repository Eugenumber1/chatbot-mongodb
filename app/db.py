from motor.motor_asyncio import AsyncIOMotorClient
import os
from urllib.parse import quote_plus
import dotenv

dotenv.load_dotenv()

user = quote_plus(os.getenv("MONGODB_USER", "user"))
password = quote_plus(os.getenv("MONGODB_PASSWORD", "password"))
host = os.getenv("MONGODB_HOST", "mongodb")


def get_mongo_uri():
    return f"mongodb://{user}:{password}@{host}:27017"


client = AsyncIOMotorClient(get_mongo_uri())
db = client["chatbot"]

sessions = db.sessions
records = db.records
