#! /usr/bin/python3
import configparser
from sqlalchemy import create_engine, Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.dialects.mysql import DATETIME, TIMESTAMP, TEXT, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import mimetypes
import logging
import urllib.request
import magic
import os
import re
from bs4 import BeautifulSoup, SoupStrainer
from dbmodel import Expression, Manifestation, Fingerprint, Base, WikimediaItems, EuropeanaItems

config = configparser.ConfigParser()
config.read('washroom.conf')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)8s  %(message)s')
log = logging.getLogger('washroom')

engine = create_engine(config['washroom']['db'])

Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

#
# This list of allowed licenses give the canonical uri for the license
# followed by a number of regular expressions which should match against
# that canonical license.
#
allowed_licenses = {
  'http://creativecommons.org/licenses/by/4.0/':
       [r'http://creativecommons.org/licenses/by/4\.0.*'],
  'http://creativecommons.org/licenses/by/3.0/':
       [r'http://creativecommons.org/licenses/by/3\.0.*'],
  'http://creativecommons.org/licenses/by/2.5/':
       [r'http://creativecommons.org/licenses/by/2\.5.*'],
  'http://creativecommons.org/licenses/by/2.0/':
       [r'http://creativecommons.org/licenses/by/2\.0.*'],
  'http://creativecommons.org/licenses/by/1.0/':
       [r'http://creativecommons.org/licenses/by/1\.0.*'],

  'http://creativecommons.org/licenses/by-sa/4.0/':
       [r'http://creativecommons.org/licenses/by-sa/4\.0.*'],
  'http://creativecommons.org/licenses/by-sa/3.0/':
       [r'http://creativecommons.org/licenses/by-sa/3\.0.*'],
  'http://creativecommons.org/licenses/by-sa/2.5/':
       [r'http://creativecommons.org/licenses/by-sa/2\.5.*'],
  'http://creativecommons.org/licenses/by-sa/2.0/':
       [r'http://creativecommons.org/licenses/by-sa/2\.0.*'],
  'http://creativecommons.org/licenses/by-sa/1.0/':
       [r'http://creativecommons.org/licenses/by-sa/1\.0.*'],

  'http://creativecommons.org/licenses/by-nd/4.0/':
       [r'http://creativecommons.org/licenses/by-nd/4\.0.*'],
  'http://creativecommons.org/licenses/by-nd/3.0/':
       [r'http://creativecommons.org/licenses/by-nd/3\.0.*'],
  'http://creativecommons.org/licenses/by-nd/2.5/':
       [r'http://creativecommons.org/licenses/by-nd/2\.5.*'],
  'http://creativecommons.org/licenses/by-nd/2.0/':
       [r'http://creativecommons.org/licenses/by-nd/2\.0.*'],
  'http://creativecommons.org/licenses/by-nd/1.0/':
       [r'http://creativecommons.org/licenses/by-nd/1\.0.*'],

  'http://creativecommons.org/licenses/by-nc/4.0/':
       [r'http://creativecommons.org/licenses/by-nc/4\.0.*'],
  'http://creativecommons.org/licenses/by-nc/3.0/':
       [r'http://creativecommons.org/licenses/by-nc/3\.0.*'],
  'http://creativecommons.org/licenses/by-nc/2.5/':
       [r'http://creativecommons.org/licenses/by-nc/2\.5.*'],
  'http://creativecommons.org/licenses/by-nc/2.0/':
       [r'http://creativecommons.org/licenses/by-nc/2\.0.*'],
  'http://creativecommons.org/licenses/by-nc/1.0/':
       [r'http://creativecommons.org/licenses/by-nc/1\.0.*'],

  'http://creativecommons.org/licenses/by-nc-sa/4.0/':
       [r'http://creativecommons.org/licenses/by-nc-sa/4\.0.*'],
  'http://creativecommons.org/licenses/by-nc-sa/3.0/':
       [r'http://creativecommons.org/licenses/by-nc-sa/3\.0.*'],
  'http://creativecommons.org/licenses/by-nc-sa/2.5/':
       [r'http://creativecommons.org/licenses/by-nc-sa/2\.5.*'],
  'http://creativecommons.org/licenses/by-nc-sa/2.0/':
       [r'http://creativecommons.org/licenses/by-nc-sa/2\.0.*'],
  'http://creativecommons.org/licenses/by-nc-sa/1.0/':
       [r'http://creativecommons.org/licenses/by-nc-sa/1\.0.*'],

  'http://creativecommons.org/licenses/by-nc-nd/4.0/':
       [r'http://creativecommons.org/licenses/by-nc-nd/4\.0.*'],
  'http://creativecommons.org/licenses/by-nc-nd/3.0/':
       [r'http://creativecommons.org/licenses/by-nc-nd/3\.0.*'],
  'http://creativecommons.org/licenses/by-nc-nd/2.5/':
       [r'http://creativecommons.org/licenses/by-nc-nd/2\.5.*'],
  'http://creativecommons.org/licenses/by-nc-nd/2.0/':
       [r'http://creativecommons.org/licenses/by-nc-nd/2\.0.*'],
  'http://creativecommons.org/licenses/by-nc-nd/1.0/':
       [r'http://creativecommons.org/licenses/by-nc-nd/1\.0.*'],
}

def valid_license(uri):
   for k,v in allowed_licenses.items():
      for row in v:
          if (re.match(row, uri)):
             return k
   return None

log.debug('Initialized')
# 
#  Here's the main principle of the washroom:
#
#   1. Check all works in Expression, compare updated time against
#      the last change time of origin. (=> UPDATED if outdated
#      by timestamp, => DELETE if source work disappears)
#   2. Check all works in origin which do not exist in Expression
#      (=> NEW WORKS)
#
####
## Europeana
####
log.info('Starting work on Europeana')
cbase = "http://europeana.eu/"

entity = session.query(Expression).filter(Expression.collection_url == cbase).all()
for row in entity:
  srcwork = session.query(EuropeanaItems).filter(EuropeanaItems.europeana_id == row.source_id).first()
  if not srcwork:
     session.delete(row)
     session.commit()
  elif srcwork.updated_date > row.updated_date:
     session.query(Expression).filter(Expression.id == row.id).update(
                { Expression.title: srcwork.title,
                  Expression.description: srcwork.description,
                  Expression.rights_statement: srcwork.rights_statement,
                  Expression.credit: srcwork.credit })
     session.commit()


log.info('First pass Europeana complete')
entity = session.query(EuropeanaItems).all()
for row in entity:
   expwork = session.query(Expression).filter(Expression.source_id == row.europeana_id, Expression.collection_url == cbase).first()
   if not expwork:
      obj = Expression(rights_statement = row.rights_statement,
                    source_id = row.europeana_id,
                    credit = row.credit,
                    title = row.title,
                    collection_url = cbase)
      session.add(obj)
      session.commit()
      session.refresh(obj)
      mime_type = mimetypes.guess_type(row.source_url)[0]
      obj_man = Manifestation(url = row.source_url, expression_id = obj.id,
                              media_type = mime_type)
      session.add(obj_man)
      session.commit()

log.info('Europeana complete and updated')

## Wikimedia
cbase = 'http://commons.wikimedia.org/'
log.info('Starting work on Wikimedia Commons')

# First order of business: get all works with mime type 'application/ogg'
# as we have no clue if they are audio or video. Only way to know is to
# retrieve each work and process it with filemagic
#
m = magic.Magic(flags=magic.MAGIC_MIME_TYPE)

entity = session.query(WikimediaItems).filter(WikimediaItems.mime == 'application/ogg', WikimediaItems.derived_mime == None)
n = 0
for row in entity.all():
  n = n + 1
  log.debug('Requesting')
  try:
    filename, headers = urllib.request.urlretrieve(row.url)
  except urllib.error.HTTPError:
    continue
  log.debug('Identifying')
  l = m.id_filename(filename)
  if l == 'audio/ogg' or l == 'video/ogg':
     log.debug('Identified id %d as %s' % (row.id, l))
     session.query(WikimediaItems).filter(WikimediaItems.id == row.id).update({ WikimediaItems.derived_mime: l })
  if n % 100 == 0:
     session.commit()
  os.unlink(filename)
session.commit()

#   1. Check all works in Expression, compare updated time against
#      the last change time of origin. (=> UPDATED if outdated
#      by timestamp, => DELETE if source work disappears)
#   2. Check all works in origin which do not exist in Expression
#      (=> NEW WORKS)
entity = session.query(Expression).filter(Expression.collection_url == cbase).all()
for row in entity:
  srcwork = session.query(WikimediaItems).filter(WikimediaItems.title == row.source_id).first()
  if not srcwork:
     session.delete(row)
     session.commit()
  elif srcwork.updated_date > row.updated_date:
     soup = BeautifulSoup(srcwork.artist)
     artist = soup.get_text()
     link = BeautifulSoup(srcwork.artist, parseOnlyThese=SoupStrainer('a'))
     if link.has_attr('href'):
        artisturl = link['href']
     else:
        artisturl = none
     soup = BeautifulSoup(srcwork.imagedescription)
     desc = soup.get_text()
     license = valid_license(srcwork.license_url)
     if (not license):
        log.debug("Invalid license: %s" % srcwork.license_url)
        continue
     session.query(Expression).filter(Expression.id == row.id).update(
                { Expression.title: srcwork.title,
                  Expression.description: desc,
                  Expression.rights_statement: license,
                  Expression.credit: artist,
                  Expression.credit_url: artisturl })
     session.commit()

log.info('First pass Wikimedia Commons complete')

entity = session.query(WikimediaItems).all()
for row in entity:
   expwork = session.query(Expression).filter(Expression.collection_url == cbase, Expression.source_id == row.title).first()
   if not expwork:
      soup = BeautifulSoup(row.artist)
      artist = soup.get_text()
      link = BeautifulSoup(row.artist, parseOnlyThese=SoupStrainer('a'))
      if link.has_attr('href'):
         artisturl = link['href']
      else:
        artisturl = none
      soup = BeautifulSoup(row.imagedescription)
      desc = soup.get_text()
      license = valid_license(srcwork.license_url)
      if (not license):
         log.debug("Invalid license: %s" % srcwork.license_url)
         continue

      obj = Expression(rights_statement = license,
                    source_id = row.title,
                    credit = artist,
                    credit_url = artisturl,
                    description = desc,
                    title = row.title,
                    collection_url = cbase)
      session.add(obj)
      session.commit()
      session.refresh(obj)
      if (row.mime == 'application/ogg'):
         mime = row.derived_mime
      else:
         mime = row.mime

      obj_man = Manifestation(url = row.url, expression_id = obj.id,
                              media_type = mime)
      session.add(obj_man)
      session.commit()
log.debug("Finished Wikimedia Commons second pass")
