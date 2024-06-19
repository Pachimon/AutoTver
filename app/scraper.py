from collections import defaultdict

from bs4 import BeautifulSoup
from app import series_collection
from requests_html import AsyncHTMLSession
import re
import asyncio


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
        await response.html.arender(sleep=5)
        soup = BeautifulSoup(response.html.html, 'html.parser')
    finally:
        await session.close()
    return soup


async def get_series_links(soup):
    links = soup.find_all('a', href=True)
    return set([link['href'] for link in links if "/series/" in link['href']])


async def get_episode_links(soup):
    categories = {}
    containers = soup.find_all(class_=re.compile(r'^episode-live-list-column_season'))
    for container in containers:
        category_span = container.find('span')
        if category_span:
            category = category_span.text.strip()
        else:
            category = 'Unknown'
        categories[category] = {}

        links = container.find_all('a', href=True)
        episode_links = set([link['href'] for link in links if '/episodes/' in link['href']])

        for episode_link in episode_links:
            episode_title = await get_episode_info(episode_link)
            categories[category][episode_link.split('/')[-1]] = episode_title

    return categories


async def get_series_info(url):
    title_tag = soup = None
    count = 0
    while not title_tag or count > 2:
        soup = await get_soup(url)
        # series-main_title__qi7zw
        title_tag = soup.find('h1', class_=re.compile(r'^series-main_title'))
        count += 1
    return title_tag.text.strip() if title_tag else "No Title", await get_episode_links(soup)


async def get_episode_info(url):
    soup = await get_soup(url)
    if soup:
        # titles_title__KJ7tf
        title_tag = soup.find('h1', class_=re.compile(r'^titles_title'))
        if not title_tag:
            return "No Title"
        print(f"Episode: {title_tag.text.strip()}")
        return title_tag.text.strip()
    return None


async def update_series(url):
    print(f"trying for url {url}")
    soup = await get_soup(url)
    if soup:
        series_links = await get_series_links(soup)
        print(f"found {len(series_links)} series: {series_links}")
        for link in series_links:
            series_name, info = await get_series_info(link)
            print(f"found series: {series_name}, with {len(info.values())} episodes/vids")

            categories = defaultdict(lambda: False)
            for key in info:
                categories[key]
            series_id = link.split('/')[-1]

            # TODO: check for already exists and only update info?
            series_data = {
                '_id': series_id,
                'name': series_name,
                'episode': info,
                'available': [],
                'downloaded': [],
                'follow': categories
            }

            # Fetch existing data
            existing_series = series_collection.find_one({'_id': series_id})
            if existing_series:
                updated_episodes = existing_series['episode'].update(info)
                series_data['episode'] = updated_episodes

            # Send to DB
            series_collection.update_one(
                {'name': series_name},
                {'$set': series_data},
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
