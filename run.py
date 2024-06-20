from app import app
from app.tasks import scheduler, loop

from threading import Thread


if __name__ == "__main__":
    scheduler.start()

    def run_flask():
        app.run(debug=True, use_reloader=False)

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
