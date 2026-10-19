from flask import current_app
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_client = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(
            current_app.config["MONGO_URI"],
            serverSelectionTimeoutMS=3000,
        )
    return _client


def get_db():
    return get_client()[current_app.config["MONGO_DB"]]


def ping_mongo():
    get_client().admin.command("ping")


def close_mongo():
    global _client
    if _client is not None:
        _client.close()
        _client = None
