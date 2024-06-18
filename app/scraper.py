import requests
from bs4 import BeautifulSoup
from app import series_collection
from bson.objectid import ObjectId
import re


def get_soup(url):
    response = requests.get(url)
    if response.status_code == 200:
        page_content = response.content
        return BeautifulSoup(page_content, 'html.parser')
    else:
        print(f"Failed to retrieve {url}. Status code: {response.status_code}")
    return None


def get_links(soup, tag="series"):
    tag = '/' + tag + '/'
    links = soup.find_all('a', href=True)
    return [link['href'] for link in links if tag in link['href']]


def get_info(url):
    soup = get_soup(url)
    if soup:
        # series-main_title__qi7zw
        title_tag = soup.find('h1', class_=re.compile(r'^series-main_title'))
        return title_tag.text.strip(), get_links(soup, tag='episodes')
    return None


def update_series(urls):
    for url in urls:
        series_links = get_links(url)
        for link in series_links:
            series_name, info = get_info(link)
            series_data = {
                'name': series_name,
                'episode': [],
                'available': [],
                'downloaded': [],
                'follow': False
            }
            series_collection.update_one(
                {'name': series_name},
                {'$setOnInsert': series_data},
                upsert=True
            )


def update_database():
    variety_url = 'http://tver.jp/categories/variety'
    drama_url = 'http://tver.jp/categories/drama'
    update_series([variety_url, drama_url])


# Example usage
if __name__ == "__main__":
    update_database()
