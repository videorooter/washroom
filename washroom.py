#! /usr/bin/python3
import configparser
from sqlalchemy import create_engine, Column, Integer, Sequence, String, ForeignKey
from sqlalchemy.dialects.mysql import DATETIME, TIMESTAMP, TEXT, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

config = configparser.ConfigParser()
config.read('washroom.conf')

engine = create_engine(config['washroom']['db'])
Base = declarative_base()

class EuropeanaItems(Base):
    __tablename__ = 'europeana_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    # 
    # media_type:  image/jpeg image/gif  image/png video/mpeg video/mp4
    #              video/ogg  video/webm audio/ogg
    #
    media_type = Column(String(64))
    credit = Column(String(500))
    credit_url = Column(String(1024))
    #
    # http://wikimedia.org/
    #
    collection_url = Column(String(128))
    source_url = Column(String(256))
    updated_date = Column(TIMESTAMP, default=datetime.utcnow,
                          nullable=False, onupdate=datetime.utcnow)
    manifestation = relationship('Manifestation', backref="expression")

class Manifestation(Base):
    __tablename__ = 'manifestation'
    url = Column(String(255), primary_key = True)
    expression_id = Column(INTEGER(unsigned=True, zerofill=True), 
                     ForeignKey('expression.id'))
    fingerprint = relationship('Fingerprint', backref="manifestation")

class Fingerprint(Base):
    __tablename__ = 'fingerprint'
    url = Column(String(255), ForeignKey('manifestation.url'),
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
 
Base.metadata.create_all(engine)
dbsession = sessionmaker(bind=engine)
session = dbsession()

# 
#  Here's the main principle of the washroom:
#
#   1. Check all works in Expression, compare updated time against
#      the last change time of origin. (=> UPDATED if outdated
#      by timestamp)
#   2. Check all works in origin, updated since the last expression
#      was updated  (=> NEW WORKS)
#   3. Check all fingerprints for all manifestations of all works
#      and if older than X months, re-calculate?

# 2. Check all works in article_images, updated since last in works
#entity = session.query(Work.updated_date).filter(Work.work_origin == wmbase).order_by(Work.updated_date.desc()).first()
#if not entity:
#    last_date = 0
#else:
#    last_date = entity.updated_date

#entity = session.query(ArticleImages.id).filter(ArticleImages.inserted_date > last_date).order_by(ArticleImages.updated_date).limit(1000).all()
#for row in entity:
#  print(row.id)
