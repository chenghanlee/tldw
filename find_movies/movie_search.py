import gdata.youtube
import gdata.youtube.service
import tmdb
import sys

sys.path.append("../movie_trailers/models")

from amazon_product_search import AmazonProductSearch
from format_string import format_string
from rottentomatoes import RT

# crawler specific imports
from dateutil import parser
from Movie import Actor, Metadata, Movie, Review
from upload_to_s3 import create_thumbnail


class MovieInfo(object):
    def __init__(self, movie, rotten_tomatoe_api_key, tmdb_api_key,
        aws_access_key, aws_secret_key, affiliate_key):
        self._movie = movie
        # amazon
        self._amazon_product_search = AmazonProductSearch(aws_access_key,
                                        aws_secret_key, affiliate_key)
        # rotten tomatoes
        self._rt = RT(rotten_tomatoe_api_key)
        self._rt_data = self._rt.search(movie)[0]
        # tmdb
        self._tmdb = tmdb
        self._tmdb.configure(tmdb_api_key)
        movie = self._tmdb.Movies(movie, limit=True).get_best_match()
        self._tmdb_data = self._tmdb.Movie(movie[1]['id'])
        # youtube
        self._yt_service = gdata.youtube.service.YouTubeService()

    def get_amazon_purchase_links(self, top_cast, runtime):
        return self._amazon_product_search.item_search(self._movie, 
                                            top_cast, runtime)
    @property
    def cast(self):
        '''
        Returns the names of the full cast for this movie
        '''

        full_cast = self._rt.info(self._rt_data['id'], 'cast')
        names = [cast['name'] for cast in full_cast['cast']]
        return names

    @property
    def critic_reviews(self):
        '''
        Returns a list of critic reviews for this movie. The list
        is componsed of json document.
        '''

        reviews = self._rt.info(self._rt_data['id'], 'reviews')
        return reviews['reviews']

    @property
    def critics_score(self):
        '''
        Returns the rotten tomatoe critic score for this movie
        '''
        return self._rt_data['ratings']['critics_score']

    @property
    def director(self):
        '''
        Returns a list of directors for this movie
        '''

        return self._tmdb_data.get_director()

    @property
    def genres(self):
        '''
        Returns the genres of this movie, supplied by tmdb
        '''

        genres = self._tmdb_data.get_genres()
        genres = [genre['name'] for genre in genres]
        return genres

    @property
    def imdb_id(self):
        '''
        Returns a list of directors for this movie
        '''

        return "tt" + self._rt_data['alternate_ids']['imdb']

    @property
    def poster(self):
        '''
        Returns the poster of the movie, in its original size
        '''
        return self._tmdb_data.get_poster()

    @property
    def runtime(self):
        '''
        Return the runtime of this movie in minues
        '''

        return self._rt_data['runtime']

    @property
    def release_date(self):
        '''
        Returns this movie's release date in {year}-{month}-{day} format
        '''
        return parser.parse(self._rt_data['release_dates']['theater'])

    @property
    def similar_movies(self):
        '''
        Returns a list of imdb ids of movies that are similar to this one
        '''

        movies = self._rt.info(self._rt_data['id'], 'similar')['movies']
        tmdb_ids = ['tt' + movie['alternate_ids']['imdb'] for movie in movies]
        return tmdb_ids

    @property
    def synopsis(self):
        '''
        Returns this movie's synopsis
        '''

        return self._rt_data['synopsis']

    @property
    def title(self):
        '''
        Returns this movie's title
        '''

        return self._rt_data['title']

    @property
    def trailers(self, limit=4):
        trailers = self._tmdb_data.get_trailers()['youtube']
        if trailers > 3:
            youtube_ids = [trailer['source'] for trailer in trailers]
            print youtube_ids
            return youtube_ids
        else:
            release_year = self.release_date.split('-')[0]
            query = gdata.youtube.service.YouTubeVideoQuery()
            query.vq = "{title} {release_year} trailer".format(
                            title=self._movie, release_year=release_year)
            query.orderby = 'relevance'
            query.racy = 'include'
            feed = self._yt_service.YouTubeQuery(query)
            youtube_ids = [_extract_youtube_id(entry.media.player.url)
                                for entry in feed.entry[:limit]]
            print youtube_ids
            return youtube_ids

    def _extract_youtube_id(youtube_url):
        video_id = youtube_url.split('v=')[1]
        ampersand_position = video_id.find('&')
        if(ampersand_position != -1):
          video_id = video_id[0:ampersand_position]
        return video_id

    def save_to_swyftype(self):
        pass

def convert_amazon_purchase_link_json_to_obj(purchase_links):
    # amazon purchase link
    list_of_purchase_links = []
    for link in purchase_links:
        ASIN = link['ASIN']
        binding = link['binding']
        url = link['DetailPageURL']    
        new_purchase_link = PurchaseLink(_ASIN=ASIN, _media_type=binding,
                                         _url=url)
        list_of_purchase_links.append(new_purchase_link)
    return list_of_purchase_links

def convert_cast_json_to_obj(casts):
    actors = []
    for name in casts:
        new_actor = Actor(_name=name, _formatted_name=format_string(name))
        new_actor.save()
        actors.append(new_actor)
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

if __name__ == "__main__":
    # AMAZON
    AWS_ACCESS_KEY = 'AKIAJQ3N2TVP5EAVVLJA'
    AWS_SECRET_KEY = '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'
    AWS_AFFILIATE_KEY = 'helppme-20'

    #API
    ROTTEN_TOMATOES_API_KEY = 'n298xcf5bkxf4qtnbmw7364x'
    TMDB_API_KEY = 'f43cd8f01703edd5a67e40027e5d4055'
    
    title = "toy story 3"
    movie = MovieInfo(title, ROTTEN_TOMATOES_API_KEY, TMDB_API_KEY,
                AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_AFFILIATE_KEY)

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
    trailers = movie.trailers # need to parse out the youtube ids
    amazon_purchase_links = movie.get_amazon_purchase_links(cast[0], runtime)
    print amazon_purchase_links

    # process some data that we need to save into the movie
    cast = convert_cast_json_to_obj(cast)
    formatted_director = format_string(movie.director)
    formatted_title = format_string(title)
    reviews = convert_review_json_to_obj(reviews)
    metadata = convert_to_metadata(imdb_id, runtime)
    thumbnail = create_thumbnail(formatted_title, poster, verbose=True)
    
    # new_movie = Movie(_director=director, _formatted_director=formatted_director,
    #                 _title=title, _formatted_title=formatted_title, 
    #                 _synopsis=synopsis, _critics_score=critics_score,
    #                 _release_date=release_date, _poster=poster,
    #                 _thumbnail=thumbnail, _cast=cast, _genres=genres,
    #                 _metadata=metadata, _reviews=reviews,
    #                 _similar_movies=similar_movies, _trailers=trailers,
    #                 _purchase_links=amazon_purchase_links)
    # new_movie.save()

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

    
