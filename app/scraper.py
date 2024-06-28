import re, os
from collections import defaultdict
from urllib.request import urlretrieve

from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession

from app import series_collection, episodes_collection

RENDER_TIME = 10  # 4 seconds fails to render sometimes
RETRY_COUNT = 3
BASE_DOMAIN = "https://tver.jp"
variety_url = 'https://tver.jp/categories/variety'
drama_url = 'https://tver.jp/categories/drama'
new_all_url = 'https://tver.jp/newer/all'
new_other_url = 'https://tver.jp/newer/other'


async def get_soup(url, render=0, scroll=0):
    if url.startswith("/series") or url.startswith("/episode"):
        url = BASE_DOMAIN + url
    print(f"Getting soup for {url=}")

    session = AsyncHTMLSession()
    try:
        response = await session.get(url)
        await response.html.arender(scrolldown=scroll, sleep=render if render else RENDER_TIME)
        soup = BeautifulSoup(response.html.html, 'html.parser')
    finally:
        await session.close()
    return soup


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
            link = episode.find('a', attrs={'href': re.compile(r'^/?episodes/\w+')})
            title = episode.find(class_=re.compile(r'^episode-row_title'))
            if link:
            # TODO: Change this to the schema below so we dont have to down below
                print(f"Episode: {title.text.strip() if title else 'No Title'}, {link['href']}")
                categories[category][link['href'].split('/')[-1]] = title.text.strip() if title else "No Title"
    return categories


async def get_series_info(url):
    title_tag = soup = None
    count = 0
    while not title_tag and count < RETRY_COUNT:
        soup = await get_soup(url)
        # series-main_title__qi7zw
        title_tag = soup.find('h1', class_=re.compile(r'^series-main_title'))
        count += 1
    img = soup.find('img', class_=re.compile(r'^thumbnail-img_img'))
    save_path = f"app/static/images/{url.split('/')[-1]}.jpg"
    if img and not os.path.exists(save_path):
        print(f"Saving Image for series: {title_tag}")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urlretrieve(img['src'], save_path)
    return title_tag.text.strip() if title_tag else "No Title", await get_episode_info(soup)


async def get_pattern_links(soup, category):
    links = soup.find_all('a', href=True)
    pattern = re.compile(rf"/{category}/[A-Za-z0-9]+$")
    return set([link['href'] for link in links if pattern.search(link['href'])])


async def update_from_urls(urls):
    series_links, episode_links = set(), set()
    for url in urls:
        soup = await get_soup(url, render=2, scroll=9)
        series_links.update(await get_pattern_links(soup, 'series'))
        episode_links.update(await get_pattern_links(soup, 'episodes'))
        print(f"{len(series_links)=}, {len(episode_links)=}")

    # Update using the first batch of series links
    print(f"found {len(series_links)} series: {series_links}")
    in_db_links = await series_links_to_database(series_links)
    print("Finished first batch")

    # Remove all the added series from first batch
    episode_links -= in_db_links

    # Find all unadded series using episode links
    print("Starting second batch from episodes")
    series_links_from_ep = set()
    for ep_link in episode_links:
        ep_soup = await get_soup(ep_link, render=6)
        ser_links = await get_pattern_links(ep_soup, 'series')
        series_links_from_ep.update(ser_links)
    print(f"found {len(series_links_from_ep)} series: {series_links_from_ep}")
    print(f"Total found {len(series_links_from_ep) + len(series_links)}")
    await series_links_to_database(series_links_from_ep)


async def series_links_to_database(series_links):
    episode_links = set()
    for link in series_links:
        series_name, info = await get_series_info(link)

        series_id = link.split('/')[-1]
        episodes = list(set([(k, name, cat) for cat, d in info.items() for k, name in d.items()]))
        episode_ids = list(set([k for k, _, _ in episodes]))
        print(f"found series: {series_name}, with {len(episode_ids)} episodes/vids")

        unavailable_query = {
            'series_id': series_id,
            '_id': {'$nin': episode_ids}
        }
        episodes_collection.update_many(unavailable_query, {'$set': {'available': False}})

        existing_series = series_collection.find_one({'_id': series_id})
        if existing_series:
            episode_ids.extend(existing_series['episodes'])
            series_data = {
                'episodes': list(set(episode_ids))
            }
        else:
            categories = dict()
            for key in info:
                categories[key] = False

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
            episode_links.add(episode[0])

            existing_episode = episodes_collection.find_one({'_id': episode[0]})
            category = episode[2]
            if existing_episode:
                episode_data = {
                    'available': True,
                    'category': category,
                    'follow': existing_series['follow'][category] if existing_series and category in existing_series['follow'] else False,
                }
            else:
                episode_data = {
                    '_id': episode[0],
                    'name': episode[1],
                    'category': category,
                    'series_id': series_id,
                    'follow': existing_series['follow'][category] if existing_series and category in existing_series['follow'] else False,
                    'available': True,
                    'downloaded': False,
                }
            episodes_collection.update_one(
                {'_id': episode[0]},
                {'$set': episode_data},
                upsert=True
            )
    return episode_links


async def update_database():
    print("starting update database")
    await update_from_urls([variety_url, drama_url, new_all_url, new_other_url])
    print("finished update database")


# Example usage
if __name__ == "__main__":
    update_database()
