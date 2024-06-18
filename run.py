from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime
import asyncio

from app import app
from app.scraper import update_database

# Create an asyncio event loop
loop = asyncio.get_event_loop()

# Configure the AsyncIOScheduler to use the event loop
scheduler = AsyncIOScheduler(event_loop=loop)
scheduler.add_job(update_database, trigger="interval", hours=1)
scheduler.add_job(update_database, trigger="date", run_date=datetime.datetime.now())
scheduler.start()

# Run the Flask app in a separate thread
if __name__ == "__main__":
    from threading import Thread

    def run_flask():
        app.run(debug=True, use_reloader=False)

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Run the asyncio event loop
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
