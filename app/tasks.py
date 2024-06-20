import datetime

import yt_dlp
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import series_collection, episodes_collection
from app.scraper import update_database

loop = asyncio.get_event_loop()
scheduler = AsyncIOScheduler(event_loop=loop)

# Default tasks
# scheduler.add_job(update_database, trigger="date", run_date=datetime.datetime.now())
scheduler.add_job(update_database, trigger="interval", hours=1)


def download_episodes(episodes):
	def my_hook(d):
		if d['status'] == 'finished':
			if 'webpage_url_basename' in d:
				episodes_collection.update_one({'_id': d['webpage_url_basename']}, {'$set': {'downloaded': True}})
			print('Done downloading, now post-processing ...')

	for episode in episodes:
		urls = ["https://tver.jp" + '/episodes/' + episode['_id']]
		series = series_collection.find_one({'_id': episode['series_id']})
		episode_name = "%(fulltitle|No Title)s" if episode['name'] == "No Title" else episode['name']
		ydl_opts = {
			'format': 'best',
			'writesubtitles': True,
			'allsubtitles': True,
			'subtitlesformat': 'srt/best',
			'progress_hooks': [my_hook],
			'outtmpl': f"/Media/{series['name']}/{episode_name}.%(ext)s"
			# 'outtmpl': f"/Media/{series['name']} - {series['_id']}/{episode_name} - {episode['_id']}.%(ext)s"
		}

		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			error_code = ydl.download(urls)


def download_job(time):
	download_requirements = {
		'follow': True,
		'available': True,
		'downloaded': False,
	}
	download_list = list(episodes_collection.find(download_requirements))
	print(f"Starting Download Job...")
	scheduler.add_job(download_episodes, args=[download_list], trigger="date", run_date=time)
