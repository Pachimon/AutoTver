import logging
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
app.config["MONGO_URI"] = "mongodb://localhost:27017/series_db"

client = MongoClient(app.config["MONGO_URI"])
db = client.tver_db
series_collection = db.series
episodes_collection = db.episodes

from app import routes

if __name__ == '__main__':
    app.run(debug=True)
