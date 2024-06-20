from collections import defaultdict
from urllib.request import urlretrieve

from bs4 import BeautifulSoup
from app import series_collection, episodes_collection
from requests_html import AsyncHTMLSession
import re, os

RENDER_TIME = 6
RETRY_COUNT = 2
BASE_DOMAIN = "https://tver.jp"
variety_url = 'https://tver.jp/categories/variety'
drama_url = 'https://tver.jp/categories/drama'


async def get_soup(url):
    if url.startswith("/series") or url.startswith("/episode"):
        url = BASE_DOMAIN + url
    print(f"Getting soup for {url=}")

    session = AsyncHTMLSession()
    try:
        response = await session.get(url)
        await response.html.arender(sleep=RENDER_TIME)
        soup = BeautifulSoup(response.html.html, 'html.parser')
    finally:
        await session.close()
    return soup


async def get_series_links(soup):
    links = soup.find_all('a', href=True)
    return set([link['href'] for link in links if "/series/" in link['href']])


async def get_episode_info(soup):
    categories = {}
    containers = soup.find_all(class_=re.compile(r'^episode-live-list-column_season'))
    for container in containers:
        category_span = container.find('span')
        if category_span:
            category = category_span.text.strip()
        else:
            category = 'Unknown'
        categories[category] = {}

        episodes = container.find_all(class_=re.compile(r'^episode-row_host'))
        for episode in episodes:
            link = episode.find('a', href=True)
            title = episode.find(class_=re.compile(r'^episode-row_title'))
            print(f"Episode: {title}, {link}")

            # TODO: Change this to the schema below so we dont have to down below
            categories[category][link['href'].split('/')[-1]] = title.text.strip() if title else "No Title"
    return categories


async def get_series_info(url):
    title_tag = soup = None
    count = 0
    while not title_tag or count < RETRY_COUNT:
        soup = await get_soup(url)
        # series-main_title__qi7zw
        title_tag = soup.find('h1', class_=re.compile(r'^series-main_title'))
        count += 1
    img = soup.find('img', class_=re.compile(r'^thumbnail-img_img'))
    print(img)
    if img:
        save_path = f"app/static/images/{url.split('/')[-1]}.jpg"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urlretrieve(img['src'], save_path)
    return title_tag.text.strip() if title_tag else "No Title", await get_episode_info(soup)


async def update_series(url):
    print(f"trying for url {url}")
    soup = await get_soup(url)
    if soup:
        series_links = await get_series_links(soup)
        print(f"found {len(series_links)} series: {series_links}")
        for link in series_links:
            series_name, info = await get_series_info(link)

            series_id = link.split('/')[-1]
            episodes = [(k, name, cat) for cat, d in info.items() for k, name in d.items()]
            episode_ids = [k for k, _, _ in episodes]
            print(f"found series: {series_name}, with {len(episode_ids)} episodes/vids")

            existing_series = series_collection.find_one({'_id': series_id})
            if existing_series:
                episode_ids.extend(existing_series['episodes'])
                series_data = {
                    'episodes': list(set(episode_ids))
                }
            else:
                categories = defaultdict(lambda: False)
                for key in info:
                    categories[key]

                series_data = {
                    '_id': series_id,
                    'name': series_name,
                    'episodes': episode_ids,
                    'follow': categories
                }

            # Send to DB
            series_collection.update_one(
                {'_id': series_id},
                {'$set': series_data},
                upsert=True
            )

            for episode in episodes:
                existing_episode = episodes_collection.find_one({'_id': episode[0]})
                if existing_episode:
                    episode_data = {
                        'available': True,
                        'category': episode[2],
                    }
                else:
                    episode_data = {
                        '_id': episode[0],
                        'name': episode[1],
                        'category': episode[2],
                        'series_id': series_id,
                        'follow': False,
                        'available': True,
                        'downloaded': False,
                    }
                episodes_collection.update_one(
                    {'_id': episode[0]},
                    {'$set': episode_data},
                    upsert=True
                )


async def update_database():
    print("starting update database")
    await update_series(drama_url)
    await update_series(variety_url)
    print("finished update database")


# Example usage
if __name__ == "__main__":
    update_database()
