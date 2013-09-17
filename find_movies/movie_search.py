import gdata.youtube
import gdata.youtube.service
import tmdb

from amazon_product_search import AmazonProductSearch
from dateutil import parser
from rottentomatoes import RT

class MovieInfo(object):
    def __init__(self, movie, rotten_tomatoe_api_key, tmdb_api_key,
        aws_access_key, aws_secret_key, affiliate_key, rt_id=None, tmdb_id=None):
        self._movie = movie
        # amazon
        self._amazon_product_search = AmazonProductSearch(aws_access_key,
                                        aws_secret_key, affiliate_key)
        # rotten tomatoes
        self._rt = RT(rotten_tomatoe_api_key)
        if rt_id:
            self._rt_data = self._rt.info(rt_id)
        else:    
            self._rt_data = self._rt.search(movie)[0]
        # tmdb
        self._tmdb = tmdb
        self._tmdb.configure(tmdb_api_key)
        movie = self._tmdb.Movies(movie, limit=True).get_best_match()
        self._tmdb_data = self._tmdb.Movie(movie[1]['id'])
        # youtube
        self._yt_service = gdata.youtube.service.YouTubeService()

    def get_amazon_purchase_links(self, top_cast, runtime):
        products = self._amazon_product_search.item_search(self._movie, 
                        top_cast, runtime)
        return products

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

        '''
        TODO CHLEE: Convert similar movies to using movie dictionaries rather
        than a list of imdb ids. Need the title as well for doing a depth
        first search through the movie graph.
        '''
        movies = self._rt.info(self._rt_data['id'], 'similar')['movies']
        return movies

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
    def trailers(self, limit=2):
        trailers = self._tmdb_data.get_trailers()['youtube']
        if len(trailers) > 2:
            youtube_ids = [trailer['source'] for trailer in trailers]
            return youtube_ids
        else:
            '''
            CHLEE TODO: Need to filter out repeated youtube videos
            by checking the runtime of the videos.
            '''
            release_year = str(self.release_date).split('-')[0]
            query = gdata.youtube.service.YouTubeVideoQuery()
            query.vq = "{title} {release_year} trailer".format(
                            title=self._movie, release_year=release_year)
            query.orderby = 'relevance'
            query.racy = 'include'
            feed = self._yt_service.YouTubeQuery(query)
            youtube_ids = [self._extract_youtube_id(entry.media.player.url)
                            for entry in feed.entry[:limit]]
            return youtube_ids

    def _extract_youtube_id(self, youtube_url):
        video_id = youtube_url.split('v=')[1]
        ampersand_position = video_id.find('&')
        if(ampersand_position != -1):
          video_id = video_id[0:ampersand_position]
        return video_id

    def save_to_swyftype(self):
        pass
