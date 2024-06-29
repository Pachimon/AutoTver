import logging
import os

from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

# Setup Logger
tver_logs = logging.getLogger('tver_logger')
tver_logs.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s')
console_handler.setFormatter(formatter)
tver_logs.addHandler(console_handler)
log_directory = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file_path = os.path.join(log_directory, 'log_file.log')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
tver_logs.addHandler(file_handler)

# Set warning level for Flask app logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Setup Mongo DB and variables
app.config["MONGO_URI"] = "mongodb://localhost:27017/series_db"
client = MongoClient(app.config["MONGO_URI"])
db = client.tver_db
series_collection = db.series
episodes_collection = db.episodes

from app import routes

if __name__ == '__main__':
    app.run(debug=True)
