import sys
sys.path.append("../../../movie_trailers")
sys.path.append("../../../movie_trailers/models")

import settings
import swiftype

from celery import Celery
from dateutil import parser
from format_string import format_string
from Movie import db, Actor, Metadata, Movie, PurchaseLink, Review
from MovieInfo import MovieInfo
from upload_to_s3 import create_thumbnail

celery = Celery("movie_crawler.tasks")
celery.config_from_object(settings.CeleryConfig)
db_conn_settings = dict([(k.lower(), v) for k, v in
                    settings.DevConfig.MONGODB_SETTINGS.items() if v])
db.connect(**db_conn_settings)

def convert_amazon_purchase_link_json_to_obj(purchase_links):
    list_of_purchase_links = []
    for link in purchase_links:
        ASIN = link['ASIN']
        price = float(link['Amount'])/float(100)
        binding = link['Binding']
        url = link['DetailPageURL']    
        new_purchase_link = PurchaseLink(_ASIN=ASIN, _media_type=binding,
                                         _price=price, _url=url)
        list_of_purchase_links.append(new_purchase_link)
    return list_of_purchase_links

def convert_cast_json_to_obj(casts):
    actors = []
    for name in casts:
        actor = Actor.objects(_name=name).first()
        if actor is None:
            actor = Actor(_name=name, _formatted_name=format_string(name))
            actor.save()
        actors.append(actor)
    return actors

def convert_to_metadata(imdb_id, runtime):
    # movie metadata
    metadata = Metadata(_imdb_id=imdb_id, _runtime=runtime)
    return metadata

def convert_review_json_to_obj(reviews):
    list_of_reviews = []
    for review in reviews:
        critic = review['critic']
        date = parser.parse(review['date'])
        freshness = review['freshness']
        publication = review['publication']
        quote = review['quote']
        review_link = review.get('links').get('review')
        new_review = Review(_critic=critic, _date=date, _freshness=freshness,
                            _publication=publication, _quote=quote,
                            _review_link=review_link)
        list_of_reviews.append(new_review)
    return list_of_reviews

@celery.task(name='movie_crawler.index_movie', ignore_result=True,
    queue="movie_crawler")
def index_movie(movie):
    USERNAME = settings.Config.SW_EMAIL
    PASSWORD = settings.Config.SW_PASSWORD
    API_KEY = settings.Config.SW_API_KEY
    SW_ENGINE_SLUG = settings.Config.SW_ENGINE_SLUG
    client = swiftype.Client(username=USERNAME, password=PASSWORD,
                api_key=API_KEY)

    # need to format some of the data so we can save it in swyftype
    cast = [cast.name for cast in movie.cast]
    release_date = str(movie.release_date)
    release_year = release_date.split('-')[0]
    title = "{title} ({year})".format(title=movie.title, year=release_year)
    print "indexing {title}".format(title=title)
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
        pass

@celery.task(name='movie_crawler.save_movie_info_to_mongo', ignore_result=True,
    queue="movie_crawler", rate_limit="2/m")
def save_movie_info_to_mongo(title, rt_id=None, save_similar_movies=False):
    # TODO CHLEE:
    # 0000) need to conver genres to lowercase - done
    # 000) yt search returns videos with the same length for iron man - done
    # 00) Poster mistach from themoviedb - done
    # 0) No synopsis from rottentomatoe - done
    # 1) Make movie_crawler more modular and robust, so it doesn't depend
    # on settings or models from movie_trailers
    # 2) Make the functions creat_thumbnails and index_movie async tasks, so
    # that it doesn't block save_movie_info_to_mongo - done
    # 3) Need to make sure that the results returned by tmdb
    # is sorted by the differnece in days between this movie - done
    # and the expected release date
    # various API keys
    AWS_ACCESS_KEY = settings.Config.AWS_ACCESS_KEY
    AWS_SECRET_KEY = settings.Config.AWS_SECRET_KEY
    AWS_AFFILIATE_KEY = settings.Config.AWS_AFFILIATE_KEY
    ROTTEN_TOMATOES_API_KEY = settings.Config.ROTTEN_TOMATOES_API_KEY
    TMDB_API_KEY = settings.Config.TMDB_API_KEY

    # ignore request, we have previously stored this movie's information
    # in our DB
    if Movie.objects(_title=title).first() is not None:
        return

    print "searching {title}".format(title=title)
    movie = MovieInfo(title, ROTTEN_TOMATOES_API_KEY, TMDB_API_KEY,
                AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_AFFILIATE_KEY,
                rt_id=rt_id)
    # save the movie's information to the database:
    # raw movie data
    cast = movie.cast
    critics_score = movie.critics_score
    director = movie.director 
    genres = movie.genres
    imdb_id = movie.imdb_id
    poster = movie.poster
    release_date = movie.release_date
    reviews = movie.critic_reviews
    runtime = movie.runtime
    similar_movies = movie.similar_movies
    synopsis = movie.synopsis
    title = movie.title
    trailers = movie.trailers
    amazon_purchase_links = movie.get_amazon_purchase_links(cast[0], runtime)
    
    # formatting some raw data into more complex sets of data
    actors = convert_cast_json_to_obj(cast)
    formatted_director = format_string(movie.director)
    formatted_title = format_string(title)
    reviews = convert_review_json_to_obj(reviews)
    metadata = convert_to_metadata(imdb_id, runtime)
    amazon_purchase_links = convert_amazon_purchase_link_json_to_obj(
                                amazon_purchase_links)
    similar_movies_imdb_ids = []
    for similar_movie in similar_movies:
        try:
            imdb_id = 'tt' + similar_movie['alternate_ids']['imdb']
            similar_movies_imdb_ids.append(imdb_id)
        except Exception as e:
            '''
            CHLEE TODO:
            Is it possible to retrieve imdb keys for similar movies that
            rt can't find imdb keys for?
            '''
            print similar_movie
            continue
    
    thumbnail = create_thumbnail(formatted_title, poster, verbose=True)
    print thumbnail
    print "saving {title}".format(title=title)
    new_movie = Movie(_director=director,
                        _formatted_director=formatted_director,
                        _title=title, _formatted_title=formatted_title, 
                        _synopsis=synopsis, _critics_score=critics_score,
                        _release_date=release_date, _poster=poster,
                        _thumbnail=thumbnail, _cast=actors, _genres=genres,
                        _metadata=metadata, _reviews=reviews,
                        _similar_movies=similar_movies_imdb_ids,
                        _trailers=trailers,
                        _purchase_links=amazon_purchase_links)
    # new_movie.save()

    # index this movie in swyftype
    index_movie.delay(new_movie)

    # update the cast's filmography
    print "updating actor"
    for actor in actors:
        actor.update(add_to_set___filmography=new_movie.id)

    # save this movie's similar movies to mongo
    if save_similar_movies:
        for similar_movie in movie.similar_movies:
            title = similar_movie['title']
            rt_id = similar_movie['id']
            save_movie_info_to_mongo.delay(title, rt_id=rt_id, 
                save_similar_movies=True)
    
if __name__ == "__main__":
    title = "Iron Man"
    save_movie_info_to_mongo(title, save_similar_movies=True)