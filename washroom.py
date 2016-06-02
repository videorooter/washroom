#! /usr/bin/python3
import configparser
from sqlalchemy import create_engine, Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.dialects.mysql import DATETIME, TIMESTAMP, TEXT, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import mimetypes

config = configparser.ConfigParser()
config.read('washroom.conf')

engine = create_engine(config['washroom']['db'])
Base = declarative_base()

class EuropeanaItems(Base):
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

class ArticleImages(Base):
    __tablename__ = 'article_images'
    id = Column(Integer, primary_key=True, autoincrement=True)
    #
    # The title is used as a unique identifier for a work in the ETL
    # stage.
    #
    title = Column(String(150))
    userid = Column(String(100))
    img_url = Column(TEXT)
    sha1 = Column(String(150))
    artist = Column(String(250))
    object_name = Column(String(250))
    credit = Column(String(250))
    usage_terms = Column(String(250))
    license_url = Column(String(150))
    license_shortname = Column(String(250)) 
    imagedescription = Column(String(250))     
    copyrighted = Column(String(50))
    timestamp = Column(String(150))            
    continue_code = Column(String(250))  
    is_copied = Column(Integer)
    mime_type_values = Column(String(150))
    is_from_dump = Column(Integer)
    block_hash_code = Column(String(250))
    is_video = Column(Integer)
    inserted_date = Column(TIMESTAMP)
    updated_date = Column(DATETIME)
    api_from = Column(Integer)

class Expression(Base):
    __tablename__ = 'expression'
    id = Column(INTEGER(unsigned=True, zerofill=True),
                Sequence('expression_id_seq', start=1, increment=1),
                primary_key = True)
    title = Column(String(500))
    description = Column(String(2048))
    # 
    # Allowed:  Any CC URI + defined by rightsstatements.org
    #
    rights_statement = Column(String(128))
    credit = Column(String(500))
    credit_url = Column(String(1024))
    #
    # http://wikimedia.org/
    #
    collection_url = Column(String(128))
    source_id = Column(String(256))
    updated_date = Column(TIMESTAMP, default=datetime.utcnow,
                          nullable=False, onupdate=datetime.utcnow)
    manifestation = relationship('Manifestation', backref="expression")

class Manifestation(Base):
    __tablename__ = 'manifestation'
    id = Column(INTEGER(unsigned=True, zerofill=True),
                Sequence('manifestation_id_seq', start=1, increment=1),
                primary_key = True)
    url = Column(String(500))
    # 
    # media_type:  image/jpeg image/gif  image/png video/mpeg video/mp4
    #              video/ogg  video/webm audio/ogg
    #
    media_type = Column(String(64))
    expression_id = Column(INTEGER(unsigned=True, zerofill=True), 
                     ForeignKey('expression.id'))
    fingerprint = relationship('Fingerprint', backref="manifestation")

class Fingerprint(Base):
    __tablename__ = 'fingerprint'
    id = Column(INTEGER(unsigned=True, zerofill=True),
                Sequence('fingerprint_id_seq', start=1, increment=1),
                primary_key = True)
    #
    # type
    #   application/x-blockhash (default image algo)
    #   application/x-blockhash-video-j (video algo from jonaso w/ bh)
    #
    type = Column(String(64))
    hash = Column(String(256))
    updated_date = Column(TIMESTAMP, default=datetime.utcnow,
                          nullable=False, onupdate=datetime.utcnow)
    manifestation_id = Column(INTEGER(unsigned=True, zerofill=True), 
                     ForeignKey('manifestation.id'))
 
Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

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


# 
entity = session.query(EuropeanaItems).all()
for row in entity:
   expwork = session.query(Expression).filter(Expression.source_id == row.europeana_id).first()
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
