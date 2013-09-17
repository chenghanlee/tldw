import sys
sys.path.append("../movie_trailers/models")
sys.path.append("../movie_trailers")

import settings

from dateutil import parser
from extensions import celery
from format_string import format_string
from Movie import Actor, Metadata, Movie, PurchaseLink, Review
from movie_search import MovieInfo
from upload_to_s3 import create_thumbnail


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

@celery.task(name='save_movie_info_to_db', ignore_result=True,
    queue="movie_crawler")
def save_movie_info_to_mongo(movie):
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
    
    # formatting some of the raw data into a more complex set of data
    cast = convert_cast_json_to_obj(cast)
    formatted_director = format_string(movie.director)
    formatted_title = format_string(title)
    reviews = convert_review_json_to_obj(reviews)
    metadata = convert_to_metadata(imdb_id, runtime)
    amazon_purchase_links = convert_amazon_purchase_link_json_to_obj(
                                amazon_purchase_links)
    similar_movies_imdb_ids = ['tt' + movie['alternate_ids']['imdb']
                                for movie in similar_movies]
    thumbnail = create_thumbnail(formatted_title, poster, verbose=True)
    
    new_movie = Movie(_director=director,
                        _formatted_director=formatted_director,
                        _title=title, _formatted_title=formatted_title, 
                        _synopsis=synopsis, _critics_score=critics_score,
                        _release_date=release_date, _poster=poster,
                        _thumbnail=thumbnail, _cast=cast, _genres=genres,
                        _metadata=metadata, _reviews=reviews,
                        _similar_movies=similar_movies_imdb_ids,
                        _trailers=trailers,
                        _purchase_links=amazon_purchase_links)
    new_movie.save()

    for actor in cast:
        actor.update(add_to_set___filmography=new_movie.id)

    # 1) need to get poster of this movie and resize it and upload 
    #    to amazon s3
    # 2) need to convert actor names and categories to lower cases
    #    and convert spaces to dashes
    # 3) need to convert movie title to lower cases and convert
    #    spaces to dashes
    # 4) need to save movie_id in the actors objects that we created
    # 4) need to save movie into swiftype searchable documents
    # print poster
    # print movie.amazon_purchase_links(cast[0])

if __name__ == "__main__":
    # AMAZON and API keys
    AWS_ACCESS_KEY = settings.Config.AWS_ACCESS_KEY
    AWS_SECRET_KEY = settings.Config.AWS_SECRET_KEY
    AWS_AFFILIATE_KEY = settings.Config.AWS_AFFILIATE_KEY
    ROTTEN_TOMATOES_API_KEY = settings.Config.ROTTEN_TOMATOES_API_KEY
    TMDB_API_KEY = settings.Config.TMDB_API_KEY
    
    title = "toy story 3"
    movie = MovieInfo(title, ROTTEN_TOMATOES_API_KEY, TMDB_API_KEY,
                AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_AFFILIATE_KEY)

    '''
    CHLEE TODO: 
    Need to update celery config and celeryd worker so the async 
    job below runs at some delayed rate, i.e. once every 1 minute
    '''
    queue = []
    queue.append(movie)
    while(len(queue) > 0):
        movie = queue.pop(0)
        save_movie_info_to_mongo.apply_async(movie)
        for similar_movie in movie.similar_movies:
            '''
            CHLEE TODO: 
            This for loop is not async and it may cause the queue
            to be filled faster than the celery workers can
            process the jobs in the queue.

            How can we incorporate the for loop into the async job?
            '''

            title = similar_movie['title']
            rt_id = similar_movie['id']
            if Movie.objects(_title=title).first() is None:
                new_movie = MovieInfo(title, ROTTEN_TOMATOES_API_KEY,
                                        TMDB_API_KEY, AWS_ACCESS_KEY,
                                        AWS_SECRET_KEY, AWS_AFFILIATE_KEY,
                                        rt_id=rt_id)
                queue.append(new_movie)
