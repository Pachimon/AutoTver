from bs4 import BeautifulSoup
from app import series_collection
from requests_html import AsyncHTMLSession
import re


BASE_DOMAIN = "https://tver.jp"
variety_url = 'https://tver.jp/categories/variety'
drama_url = 'https://tver.jp/categories/drama'


async def get_soup(url):
    if url.startswith("/series") or url.startswith("/episode"):
        url = BASE_DOMAIN + url
    print(f"Getting soup for {url=}")
    session = AsyncHTMLSession()
    response = await session.get(url)
    await response.html.arender(sleep=4)

    soup = BeautifulSoup(response.html.html, 'html.parser')
    return soup


async def get_series_links(soup):
    links = soup.find_all('a', href=True)
    print(f"{[link['href'] for link in links]=}")
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
        categories[category] = []

        links = container.find_all('a', href=True)
        episode_links = set([link['href'] for link in links if '/episodes/' in link['href']])

        for episode_link in episode_links:
            episode_title = await get_episode_info(episode_link)
            categories[category].append((episode_title, episode_link))

    return categories


async def get_series_info(url):
    soup = await get_soup(url)
    if soup:
        # series-main_title__qi7zw
        title_tag = soup.find('h1', class_=re.compile(r'^series-main_title'))
        return title_tag.text.strip(), await get_episode_links(soup)
    return None


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
            series_data = {
                'name': series_name,
                'episode': info,
                'available': [],
                'downloaded': [],
                'follow': False
            }

            # Fetch existing data
            existing_series = series_collection.find_one({'name': series_name})
            if existing_series:
                # Merge the episode lists without duplication
                updated_episodes = existing_series['episode'].update(info)
                series_data['episode'] = updated_episodes

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
