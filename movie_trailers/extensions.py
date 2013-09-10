import celery
import redis

from flask.ext.mongoengine import MongoEngine

celery = celery.Celery()
db = MongoEngine()
redis = redis.StrictRedis(host='localhost', port=6379, db=0)