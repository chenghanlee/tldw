import celery
import redis
import os
import urlparse

from flask.ext.mongoengine import MongoEngine

celery = celery.Celery()
db = MongoEngine()

REDISCLOUD_URL = os.environ.get('REDISCLOUD_URL')
if REDISCLOUD_URL:
	url = urlparse.urlparse(REDISCLOUD_URL)
	redis = redis.Redis(host=url.hostname, port=url.port, password=url.password)
else:
	redis = redis.StrictRedis(host='localhost', port=6379, db=0)