#! /usr/bin/python3
import configparser
from sqlalchemy import create_engine, Column, Integer, Sequence, String, ForeignKey, or_, func, distinct
from sqlalchemy.dialects.mysql import DATETIME, TIMESTAMP, TEXT, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import mimetypes
import urllib.request
import magic
import os
from dbmodel import Expression, Manifestation, Fingerprint, Base, WikimediaItems, EuropeanaItems
from tabulate import tabulate
from json import dumps
from bson import json_util


config = configparser.ConfigParser()
config.read("%s/%s" % (os.path.dirname(os.path.realpath(__file__)), 'washroom.conf'))

engine = create_engine(config['washroom']['db'])

Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

collections = { 'http://europeana.eu/': {
                    'name': 'Europeana',
                    'shortname': 'europeana' },
                'http://commons.wikimedia.org/': {
                    'name': 'Wikimedia Commons',
                    'shortname': 'wmc' }
              }

for k,v in collections.items():
   d = []
   query = session.query(Expression).filter(Expression.collection_url == k).all()
   for e in query:
      c = []
      for m in e.manifestation:
          b = []
          for f in m.fingerprint:
              b.append({ "type": f.type,
                         "hash": f.hash,
                         "updated_date": f.updated_date })
          c.append({ "fingerprint": b,
                     "media_type": m.media_type,
                     "url": m.url })
      a = { "title": e.title,
            "id": e.id,
            "credit": e.credit,
            "credit_url": e.credit_url,
            "description": e.description,
            "rights_statement": e.rights_statement,
            "source_id": e.source_id,
            "collection_url": e.collection_url,
            "updated_date": e.updated_date,
            "manifestation": c }
      d.append(a)
   f = open("%s/export_%s.json" % (config['washroom']['exportdir'], v['shortname']), "w")
   f.write(dumps(d, default=json_util.default))
   f.close()
   f = open("%s/export_%s_pp.json" % (config['washroom']['exportdir'], v['shortname']), "w")
   f.write(dumps(d, default=json_util.default, sort_keys=True,indent=4))
   f.close()
