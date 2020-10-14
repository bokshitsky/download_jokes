from sqlalchemy import create_engine, MetaData, Table, Text, BigInteger, Column, Integer, UniqueConstraint

meta = MetaData()

jokes = Table(
    'jokes', meta,
    Column('id', Integer, primary_key=True),
    Column('body', Text, nullable=False),
    Column('type', Integer, nullable=False),
    Column('snapshot', Text, nullable=False),
    UniqueConstraint('snapshot', sqlite_on_conflict='IGNORE')
)
