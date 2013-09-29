import sys
sys.path.append("../../../movie_trailers")
sys.path.append("../../../movie_trailers/models")

import os
import requests
import settings
import swiftype

from bs4 import BeautifulSoup
from celery import Celery
from find_actor_info import find_actor_info
from format_string import format_string
from Movie import db, Actor, Movie
from urllib import urlencode
from upload_to_s3 import download_image, upload_to_s3

celery = Celery("movie_crawler.tasks")
celery.config_from_object(settings.CeleryConfig)
db_conn_settings = dict([(k.lower(), v) for k, v in
                    settings.ProdConfig.MONGODB_SETTINGS.items() if v])
db.connect(**db_conn_settings)


@celery.task(name='movie_crawler.create_thumbnail', ignore_result=True,
    queue="movie_crawler")
def create_thumbnail(movie_title, movie_poster, verbose=False):
    if verbose:
        print "creating thumbnail for {movie}".format(movie=movie_title)
    filename = movie_title + '.jpg'
    download_image(movie_poster, filename)
    s3_url = upload_to_s3(filename, 'tldw', 'images/thumbnails', verbose=True)
    s3_url = "http://s3.amazonaws.com/tldw/" + s3_url
    os.remove(filename)
    return s3_url

@celery.task(name='movie_crawler.index_movie', ignore_result=True,
    queue="movie_crawler")
def index_movie(movie, verbose=False):
    if verbose:
        print "indexing {title}".format(title=movie.title)
    
    USERNAME = settings.Config.SW_EMAIL
    PASSWORD = settings.Config.SW_PASSWORD
    API_KEY = settings.Config.SW_API_KEY
    SW_ENGINE_SLUG = settings.Config.SW_ENGINE_SLUG

    # need to format some of the data so we can save it in swyftype
    cast = [cast.name for cast in movie.cast]
    release_year = str(movie.release_date).split('-')[0]
    title = "{title} ({year})".format(title=movie.title, year=release_year)
    
    client = swiftype.Client(username=USERNAME, password=PASSWORD,
                api_key=API_KEY)
    try:
        client.create_document(SW_ENGINE_SLUG, 'trailer', {
            'external_id':  movie.formatted_title,
            'fields': [
                {'name': 'title', 'value': movie.title, 'type': 'string'},
                {'name': 'cast', 'value': cast, 'type': 'enum'},
                {'name': 'genres', 'value': movie.genres, 'type': 'enum'},
                {'name': 'synopsis', 'value': movie.synopsis, 'type': 'text'},
                {'name': 'critic score', 'value': movie.critics_score, 'type': 'integer'},
                {'name': 'release_date', 'value': release_date, 'type': 'date'},
                {'name': 'runtime', 'value': movie.metadata.runtime, 'type': 'integer'},
                {'name': 'url', 'value': movie.url, 'type': 'enum'},
            ]
        })
    except:
        print "couldn't index {title}".format(title=title)

@celery.task(name='movie_crawler.update_actor_bio_and_picture', ignore_result=True,
    queue="movie_crawler", rate_limit="6/m")
def update_actor_bio_and_picture(name, verbose=False):
    if verbose:
        print "finding biography and picture for {name}".format(name=name)

    info = find_actor_info(name)
    bio = info['bio']
    image_url = info['image_url']

    if bio:
        Actor.objects(_name=name).update_one(set___biography=bio)

    if image_url:
        filename = format_string(name) + ".jpg"    
        download_image(image_url, filename, width="original")
        s3_url = upload_to_s3(filename, "tldw", "images/actors")
        s3_url = "http://s3.amazonaws.com/tldw/" + s3_url
        os.remove(filename)
        Actor.objects(_name=name).update_one(set___picture=s3_url)