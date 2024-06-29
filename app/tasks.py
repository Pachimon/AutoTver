import datetime, re

import yt_dlp
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import series_collection, episodes_collection, tver_logs
from app.scraper import update_database

loop = asyncio.get_event_loop()
scheduler = AsyncIOScheduler(event_loop=loop)


def download_episodes(episodes):
	def my_hook(d):
		if d['status'] == 'finished':
			if 'info_dict' in d and 'webpage_url_basename' in d['info_dict']:
				episodes_collection.update_one({'_id': d['info_dict']['webpage_url_basename']}, {'$set': {'downloaded': True}})
			tver_logs.info(f"\nDone downloading {d['filename']} now post-processing ...")

	for episode in episodes:
		if isinstance(episode, str):
			episode = episodes_collection.find_one({'_id': episode})
		urls = ["https://tver.jp" + '/episodes/' + episode['_id']]
		series = series_collection.find_one({'_id': episode['series_id']})

		pattern = re.compile(r'[\\/]')
		episode_name = pattern.sub('-', episode['name'])
		if episode_name == "No Title":
			episode_name = "%(fulltitle|No Title)s"
		else:
			tver_logs.warning(f"{episode_name=}")

		ydl_opts = {
			'format': 'best',
			'writesubtitles': True,
			'allsubtitles': True,
			'subtitlesformat': 'srt/best',
			'progress_hooks': [my_hook],
			'outtmpl': f"/Media/{series['name']}/{episode['category']}/{episode_name}.%(ext)s"
			# 'outtmpl': f"/Media/{series['name']} - {series['_id']}/{episode_name} - {episode['_id']}.%(ext)s"
		}
		try:
			with yt_dlp.YoutubeDL(ydl_opts) as ydl:
				error_code = ydl.download(urls)
		except yt_dlp.DownloadError as e:
			# TODO: Handle this later
			tver_logs.error(e)
		except Exception as e:
			tver_logs.error(e)


def download_job(time=None):
	if not time:
		time = datetime.datetime.now()
	download_requirements = {
		'follow': True,
		'available': True,
		'downloaded': False,
	}
	download_list = list(episodes_collection.find(download_requirements))
	tver_logs.info(f"Found {len(download_list)} episodes needing to be downloaded")
	if download_list:
		tver_logs.info(f"Starting Download Job...")
		scheduler.add_job(download_episodes, args=[download_list], trigger="date", run_date=time)


# Default tasks
scheduler.add_job(update_database, trigger="date", run_date=datetime.datetime.now())
scheduler.add_job(download_job, trigger="date", run_date=datetime.datetime.now() + datetime.timedelta(minutes=50))
scheduler.add_job(update_database, trigger="interval", hours=8)
scheduler.add_job(download_job, trigger="interval", hours=9)
