import hashlib
import logging
from typing import NamedTuple

from sqlalchemy import MetaData, Table, Text, Column, Integer, UniqueConstraint

meta = MetaData()

Jokes = Table(
    'jokes', meta,
    Column('id', Integer, primary_key=True),
    Column('body', Text, nullable=False),
    Column('type', Integer, nullable=False),
    Column('snapshot', Text, nullable=False),
    Column('source', Text, nullable=True),
    UniqueConstraint('snapshot', sqlite_on_conflict='IGNORE')
)

log = logging.getLogger('model')


class JokeToInsert(NamedTuple):
    content: str
    type: int
    source: str


class JokesDb:

    def __init__(self, engine):
        self.engine = engine

    def save_joke(self, joke: JokeToInsert):
        try:
            conn = self.engine.connect()
            conn.execute(Jokes.insert().values(
                body=joke.content, snapshot=_calculate_snapshot(joke), type=joke.type, source=joke.source
            ))
            conn.close()
            return True
        except Exception as e:
            log.exception('error during save to database')
            return False


def _calculate_snapshot(joke):
    return hashlib.md5(joke.content.encode('utf-8')).hexdigest()
