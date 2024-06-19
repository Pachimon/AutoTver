import datetime
import yt_dlp
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import series_collection
from app.scraper import update_database

loop = asyncio.get_event_loop()
scheduler = AsyncIOScheduler(event_loop=loop)

# Default tasks
scheduler.add_job(update_database, trigger="date", run_date=datetime.datetime.now())
scheduler.add_job(update_database, trigger="interval", hours=1)


def download_episode(series_id, category, episode_id):
	def my_hook(d):
		if d['status'] == 'finished':
			print('Done downloading, now post-processing ...')

	urls = ["https://tver.jp" + '/episodes/' + episode_id]
	series = series_collection.find_one({'_id': series_id})
	ydl_opts = {
		'format': 'best',
		'writesubtitles': True,
		'allsubtitles': True,
		'subtitlesformat': 'srt/best',
		'progress_hooks': [my_hook],
		'outtmpl': f"/Media/{series['name']}/{series['episode'][category][episode_id]}.%(ext)s"
	}

	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		error_code = ydl.download(urls)


def download_job(time):
	# series_collection.find({'follow': })
	print(f"Starting Download Job...")
	scheduler.add_job(download_episode, args=[], trigger="date", run_date=datetime.datetime.now())