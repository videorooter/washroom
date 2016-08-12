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

config = configparser.ConfigParser()
config.read("%s/%s" % (os.path.dirname(os.path.realpath(__file__)), 'washroom.conf'))

engine = create_engine(config['washroom']['db'])

Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

collections = {'Europeana': 'http://europeana.eu/', 'Wikimedia Commons': 'http://commons.wikimedia.org/'}

print("<html><head><title>Videorooter statistics</title></head><body>")
print("<p>Last updated: %s</p>" % datetime.utcnow())
# What we want to output:
# 1.
#               Expressions Manifestations Fingerprint Failed Unprocessed
#    collection
#    collection
#
print("<h1>Videorooter main database</h1>")
print("<p>This gives an overview of the works in the videorooter database, which is included in the search API. There may be many more fingerprints than manifestations as each manifestation can be processed by one or more fingerprint algorithms. The number of unprocessed manifestations can include manifestations for which a hash can not be calculated due to it having a mime type which is not supported (ie. sound or pdfs)</p>")

headers = ["Collection", "Expressions", "Manifestations", "Fingerprints", "(Failed)", "(Unprocessed)"]
data = []

for k,v in collections.items():
   expr = session.query(Expression).filter(Expression.collection_url == v).count()
   mani = session.query(Expression,Manifestation).filter(Expression.collection_url == v, Expression.id == Manifestation.expression_id).count()
   fing = session.query(Expression,Manifestation,Fingerprint).filter(Expression.collection_url == v, Expression.id == Manifestation.expression_id, Manifestation.id == Fingerprint.manifestation_id).count()
   fingfailed = session.query(Expression,Manifestation,Fingerprint).filter(Expression.collection_url == v, Expression.id == Manifestation.expression_id, Manifestation.id == Fingerprint.manifestation_id, or_(Fingerprint.hash == 'FAILED', Fingerprint.hash == 'FAILED2')).count()

   man_ids = session.query(Fingerprint.manifestation_id).subquery('man_ids')
   fingmissing = session.query(Expression,Manifestation).filter(Expression.collection_url == v, Expression.id == Manifestation.expression_id, ~Manifestation.id.in_(man_ids)).count()
   data.append([k, expr, mani,fing,fingfailed,fingmissing])

print(tabulate(data,headers, tablefmt="html"))

#
# .              collection collection
#     mime-type   (manifestations)
#     mime-type
#
print("<h1>Overview of mime types</h1>")
print("<p>This gives an overview for each collection, which mime types are in the database.</p>")
headers = [" "]
data = []
for k,v in collections.items():
   headers.append(k)
query = session.query(distinct(Manifestation.media_type).label('media_type')).all()
for row in query:
   l = [row.media_type]
   for k,v in collections.items():
      count = session.query(Expression,Manifestation).filter(Manifestation.media_type == row.media_type, Expression.id == Manifestation.expression_id, Expression.collection_url == v).count()
      l.append(count)
   data.append(l)

print(tabulate(data,headers, tablefmt="html"))

#                collection collection
# .   license
# .   license
print("<h1>Overview of licenses</h1>")
print("<p>This gives an overview for each collection, which licenses are used.</p>")
headers = [" "]
data = []
for k,v in collections.items():
   headers.append(k)
query = session.query(distinct(Expression.rights_statement).label('uri')).all()
for row in query:
   l = [row.uri]
   for k,v in collections.items():
      count = session.query(Expression).filter(Expression.collection_url == v, Expression.rights_statement == row.uri).count()
      l.append(count)
   data.append(l)

print(tabulate(data,headers, tablefmt="html"))

print("<h1>Raw information</h1>")
print("<p>This gives some information about what the input data to Videorooter consists of. The raw information is cleaned up before being inserted into the main Videorooter database. The information available per collection vary.</p>")
# 2. Europeana
#      number of works in raw input

print("<h2>Europeana</h2>")
count = session.query(EuropeanaItems).count()
print("<p>Number of works in input: %d</p>" % count)

#
# 3. Wikimedia
#      number of works in raw input
print("<h2>Wikimedia Commons</h2>")
count = session.query(WikimediaItems).count()
print("<p>Number of works in input: %d</p>" % count)
#
#    mime-type number
#    mime-type number
print("<h3>Mime types (raw)</h3>")
query = session.query(WikimediaItems.mime, func.count(WikimediaItems.mime).label('count')).group_by(WikimediaItems.mime).all()
headers = ["Mime type", "Count"]
data = []
for row in query:
   data.append([row.mime, row.count])
print(tabulate(data,headers, tablefmt="html"))

#
#
#    derived mime number
#    derived mime number
print("<h3>Derived mime types</h3>")
print("<p>This only applies to the mime type application/ogg, which we must derive by downloading a work to figure out if it's audio or video.</p>")
query = session.query(WikimediaItems.derived_mime, func.count(WikimediaItems.derived_mime).label('count')).group_by(WikimediaItems.derived_mime).all()
headers = ["Mime type", "Count"]
data = []
for row in query:
   data.append([row.derived_mime, row.count])
print(tabulate(data,headers, tablefmt="html"))


print("</body></html>")
