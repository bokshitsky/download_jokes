from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import Jokes

FROM_FILE = '/Users/boksh/jokes.db'
TO_FILE = '/Users/boksh/jokes_anekdot_ru.db'

source = 'http://rzhunemogu.ru/RandJSON.aspx'


def main():
    FromSession = sessionmaker(bind=create_engine(f'sqlite:///{FROM_FILE}'))
    session = FromSession()
    result = session.query(Jokes.columns.body, Jokes.columns.type, Jokes.columns.snapshot).all()

    to_engine = create_engine(f'sqlite:///{TO_FILE}')
    for i, row in enumerate(result):
        to_engine.execute(Jokes.insert().values(body=row.body, snapshot=row.snapshot, type=row.type, source=source))
        print(f'success {i}')


if __name__ == '__main__':
    main()
