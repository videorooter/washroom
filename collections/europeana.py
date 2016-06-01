#! /usr/bin/python3
import configparser
from sqlalchemy import create_engine, Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.dialects.mysql import DATETIME, TIMESTAMP, TEXT, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

config = configparser.ConfigParser()
config.read('washroom.conf')

engine = create_engine(config['washroom']['db'])
Base = declarative_base()

class EuropeanaItem(Base):
    __tablename__ = 'europeana_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    europeana_id = Column(String(128))
    rights_statement = Column(String(128))
    description = Column(String(2048))
    source_url = Column(String(256))
    title = Column(String(500))
    credit = Column(String(500))
    updated_date = Column(TIMESTAMP, default=datetime.utcnow,
                          nullable=False, onupdate=datetime.utcnow)

Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

with open('output.json', encoding='utf-8') as data:
    j = json.loads(data.read())
    for item in j:
        entity = session.query(EuropeanaItem).filter(EuropeanaItem.europeana_id == item['id']).first()
        if not entity:
           obj = EuropeanaItem(rights_statement = item['rights_statement'],
                               source_url = item['source_url'],
                               credit = item['credit'],
                               title = item['title'],
                               europeana_id = item['id'])
           session.add(obj)
           session.commit()
           print("ADD: %s" % obj.source_url)
        else:
           entity.rights_statement = item['rights_statement']
           entity.credit = item['credit']
           entity.title = item['title']
           print("UPDATE: %s" % entity.source_url)
           session.commit()
