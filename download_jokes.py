import asyncio
import itertools
import json
import logging
from random import uniform
from typing import List, Callable, Awaitable

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import create_engine

from model import JokesDb, JokeToInsert, Jokes

log = logging.getLogger('crawler')


class Crawler:

    def __init__(self, db: JokesDb, jokes_fetcher: Callable[[], Awaitable[List[JokeToInsert]]]):
        self.db = db
        self.jokes_fetcher = jokes_fetcher

    async def save_jokes(self):
        jokes = await self.jokes_fetcher()
        if jokes:
            for joke in jokes:
                self.db.save_joke(joke)

    async def start(self, sleep_time_provider: Callable[[], float]):
        while True:
            await self.save_jokes()
            await asyncio.sleep(sleep_time_provider())


def saves_to_db_crawler_factory(db):
    def crawler(fetcher):
        return Crawler(db, fetcher)

    return crawler


async def http_get(session, url):
    try:
        async with session.get(url) as response:
            return await response.text()
    except Exception as e:
        log.exception(e)
        return None


async def http_post(session, url, data=None):
    try:
        async with session.post(url, data=data) as response:
            return await response.text()
    except Exception as e:
        log.exception(e)
        return None


def rzhunemogu_fetcher(*joke_types):
    """http://www.rzhunemogu.ru/FAQ.aspx
    1 - Анекдот;
    2 - Рассказы;
    3 - Стишки;
    4 - Афоризмы;
    5 - Цитаты;
    6 - Тосты;
    8 - Статусы;
    11 - Анекдот (+18);
    12 - Рассказы (+18);
    13 - Стишки (+18);
    14 - Афоризмы (+18);
    15 - Цитаты (+18);
    16 - Тосты (+18);
    18 - Статусы (+18);"""
    joke_type_generator = itertools.cycle(joke_types)

    async def fetcher():
        async with aiohttp.ClientSession() as session:
            joke_type = next(joke_type_generator)
            url = f'http://rzhunemogu.ru/RandJSON.aspx?CType={joke_type}'
            html = await http_get(session, f'http://rzhunemogu.ru/RandJSON.aspx?CType={joke_type}')
            if html and html.startswith('{"content'):
                content = html.replace('{"content":"', '').replace('"}', '')
                return [JokeToInsert(content, joke_type, url)]
            return []

    return fetcher


def anekdotru_fetcher(next_url_generator, type):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/86.0.4240.75 Safari/537.36'}

    async def fetcher():
        async with aiohttp.ClientSession(headers=headers) as session:
            url = next(next_url_generator)
            html = await http_get(session, url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                jokes = []
                for joke_div in soup.find_all('div', {'class': 'text'}):
                    jokes.append(JokeToInsert(joke_div.get_text(), type, url))
                return jokes

    return fetcher


def castlots_fetcher(type, url_part, with_hid):
    castlots_url = f'https://castlots.org/{url_part}/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, '
                      'like Gecko) Chrome/86.0.4240.75 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': castlots_url,
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://castlots.org'
    }

    url = f'https://castlots.org/{url_part}/generate.php'

    async def fetcher():
        async with aiohttp.ClientSession(headers=headers) as session:
            html = await http_post(session, url, {'hid': 'yes'} if with_hid else None)

            if html:
                data = json.loads(html)
                if not data.get('success', None):
                    return []
                body = data['va']
                return [JokeToInsert(body, type, castlots_url)]

    return fetcher


if __name__ == '__main__':
    engine = create_engine(f'sqlite:////Users/boksh/jokes.db')
    Jokes.create(engine, True)
    crawlers = saves_to_db_crawler_factory(JokesDb(engine))
    loop = asyncio.get_event_loop()

    anekdotru_random_anekdot = itertools.cycle(('http://www.anekdot.ru/random/anekdot',))
    anekdotru_random_aphorism = itertools.cycle(('http://www.anekdot.ru/random/aphorism',))
    rzhunemogu_all = rzhunemogu_fetcher(1, 2, 3, 4, 5, 6, 8, 11, 12, 13, 14, 15, 16, 18)

    loop.run_until_complete(asyncio.gather(
        crawlers(rzhunemogu_all).start(lambda: uniform(0.3, 2)),
        crawlers(rzhunemogu_all).start(lambda: uniform(0.3, 2)),
        crawlers(rzhunemogu_all).start(lambda: uniform(0.3, 2)),
        crawlers(rzhunemogu_all).start(lambda: uniform(0.3, 2)),


        crawlers(anekdotru_fetcher(anekdotru_random_anekdot, 1)).start(lambda: uniform(0.3, 1.5)),
        crawlers(anekdotru_fetcher(anekdotru_random_aphorism, 135)).start(lambda: uniform(0.3, 1.5)),

        crawlers(castlots_fetcher(1, 'generator-anekdotov-online', False)).start(lambda: uniform(0.3, 2)),
        crawlers(castlots_fetcher(1, 'generator-anekdotov-online', False)).start(lambda: uniform(0.3, 2)),
        # crawlers(castlots_fetcher(131, 'generator-komplimentov-devushke', False)).start(lambda: uniform(0.3, 2)),
        # crawlers(castlots_fetcher(132, 'generator-komplimentov-muzhchine', False)).start(lambda: uniform(0.3, 2)),
        # crawlers(castlots_fetcher(133, 'generator-interesnykh-faktov', True)).start(lambda: uniform(0.3, 2)),
        # crawlers(castlots_fetcher(134, 'generator-citat-online', False)).start(lambda: uniform(0.3, 2)),
    ))
