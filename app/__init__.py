from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/series_db"

client = MongoClient(app.config["MONGO_URI"])
db = client.series_db
series_collection = db.series

from app import routes

if __name__ == '__main__':
    app.run(debug=True)
