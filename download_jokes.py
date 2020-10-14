import asyncio
import hashlib
from random import uniform

import aiohttp
from sqlalchemy import create_engine

from model import jokes


async def fetch_by_type(session, joke_type):
    try:
        async with session.get(f'http://rzhunemogu.ru/RandJSON.aspx?CType={joke_type}') as response:
            return await response.text()
    except Exception as e:
        print(e)
        return None


DB_FILE = '/Users/boksh/jokes.db'


async def main():
    engine = create_engine(f'sqlite:///{DB_FILE}')
    jokes.create(engine, True)

    index = 1
    while True:
        for joke_type in (1, 2, 3, 4, 5, 6, 8, 11, 12, 13, 14, 15, 16, 18):
            async with aiohttp.ClientSession() as session:
                html = await fetch_by_type(session, joke_type)
                if html and html.startswith('{"content'):
                    body = html.replace('{"content":"', '').replace('"}', '')
                    snapshot = hashlib.md5(body.encode('utf-8'))

                    try:
                        conn = engine.connect()
                        conn.execute(jokes.insert().values(body=body, snapshot=snapshot.hexdigest(), type=joke_type))
                        conn.close()
                        print(f'success: {index}')
                        index += 1
                    except Exception as e:
                        print(e)

            await asyncio.sleep(uniform(0.3, 2))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

# 1 - Анекдот;
# 2 - Рассказы;
# 3 - Стишки;
# 4 - Афоризмы;
# 5 - Цитаты;
# 6 - Тосты;
# 8 - Статусы;
# 11 - Анекдот (+18);
# 12 - Рассказы (+18);
# 13 - Стишки (+18);
# 14 - Афоризмы (+18);
# 15 - Цитаты (+18);
# 16 - Тосты (+18);
# 18 - Статусы (+18);
