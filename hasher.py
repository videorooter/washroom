#! /usr/bin/python3
import configparser
from sqlalchemy import create_engine, Column, Integer, Sequence, String, ForeignKey, and_
from sqlalchemy.dialects.mysql import DATETIME, TIMESTAMP, TEXT, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import mimetypes
import time
import urllib.request
import fasteners
import subprocess
import os
from dbmodel import Expression, Manifestation, Fingerprint, Base

def lock_me():
  a_lock = fasteners.InterProcessLock('/tmp/hasher.lock')
  for i in range(10):
    gotten = a_lock.acquire(blocking=False)
    if gotten:
       time.sleep(0.2)
    else:
       time.sleep(10)

lock_me()

config = configparser.ConfigParser()
config.read('washroom.conf')

engine = create_engine(config['washroom']['db'])
Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

hashers = { 
             'http://videorooter.org/ns/blockhash': {
                'command': '/home/api/algorithms/commonsmachinery-blockhash/build/blockhash',
                'types': ['image/png', 'image/jpg'],
              },
             'http://videorooter.org/ns/x-blockhash-video-cv': {
                'command': '/home/api/algorithms/jonasob-blockhash-master/build/blockhash_video',
                'types': ['video/mp4', 'video/mpeg', 'video/ogg', 'video/webm'],
              },
          }

for k,v in hashers.items():
  man_ids = session.query(Fingerprint.manifestation_id).filter(Fingerprint.type == k).subquery('man_ids')
  q = session.query(Manifestation).filter(and_(~Manifestation.id.in_(man_ids),Manifestation.media_type.in_(v['types']))).limit(100)
  entity = q.all()
  for row in entity:
     try:
       filename, headers = urllib.request.urlretrieve(row.url)
       cmd = subprocess.check_output([v['command'], filename], stderr=subprocess.DEVNULL)
       if cmd.split()[0]:
          f = Fingerprint(type = k, hash=cmd.split()[0],
                          manifestation_id=row.id)
          session.add(f)
          session.commit()
       else:
          f = Fingerprint(type = k, hash='FAILED', # This should be more
                          manifestation_id=row.id)
          session.add(f)
          session.commit()
     except:
          f = Fingerprint(type = k, hash='FAILED2',
                          manifestation_id=row.id)
          session.add(f)
          session.commit()
     os.unlink(filename)
     print("HASH: %i type=%s, hash=%s" % (row.id, row.media_type, f.hash))
