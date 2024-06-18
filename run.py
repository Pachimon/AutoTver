from app import app, db
from app.scraper import update_database
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(func=update_database, trigger="interval", hours=1)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)
