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
        movie = self._tmdb.Movies(movie, limit=True,
                    expected_release_date=self._rt_data['release_dates']['theater']).get_best_match()
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
        genres = [genre['name'].lower() for genre in genres]
        return genres

    @property
    def imdb_id(self):
        '''
        Returns a list of directors for this movie
        '''
        try:
            return "tt" + self._rt_data['alternate_ids']['imdb']
        except:
            return self._tmdb_data.get_imdb_id()

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
        try:
            return int(self._rt_data['runtime'])
        except:
            return int(self._tmdb_data.get_runtime())

    @property
    def release_date(self):
        '''
        Returns this movie's release date in {year}-{month}-{day} format
        '''
        try:
            return parser.parse(self._rt_data['release_dates']['theater'])
        except:
            return parser.parse(self._tmdb_data.get_release_date())

    @property
    def similar_movies(self):
        '''
        Returns a list of imdb ids of movies that are similar to this one
        '''

        movies = self._rt.info(self._rt_data['id'], 'similar')['movies']
        return movies

    @property
    def synopsis(self):
        '''
        Returns this movie's synopsis
        '''
        synopsis = self._rt_data['synopsis']
        if len(synopsis) == 0:
            synopsis = self._tmdb_data.get_overview()
        return synopsis

    @property
    def title(self):
        '''
        Returns this movie's title
        '''

        return self._rt_data['title']

    @property
    def trailers(self, limit=3):
        '''
        This function returns a list of trailers related to this movie.
        
        We will use TMDB's data if it returns  3 or more trailers. If not,
        we will query youtube with the search term: "{movie_name} trailer
        {release_year}" to find the trailers.

        Returns a list of youtube ids of the trailers on youtube
        '''
        trailers = self._tmdb_data.get_trailers()['youtube']
        if len(trailers) > 2:
            return [trailer['source'] for trailer in trailers]
        else:
            release_year = str(self.release_date).split('-')[0]
            query = gdata.youtube.service.YouTubeVideoQuery()
            query.vq = "{title} trailer {release_year} ".format(
                            title=self._movie, release_year=release_year)
            query.orderby = 'relevance'
            feed = self._yt_service.YouTubeQuery(query)
            return self._remove_duplicate_yt_videos(feed, limit)
            
    def _remove_duplicate_yt_videos(self, feed, limit):
        '''
        This method removes duplicate videos by measuring the runtime
        of the videos in feed.

        If two videos are within 5 seconds of each other in runtime, 
        we assume that one of the videos is a duplicate of the other.
        '''
        videos = []
        # if the video is longer than 10 minutes, its probably not a trailer
        max_seconds = 600
        entries = filter(lambda x: x.media.duration.seconds < max_seconds,
                    feed.entry[:limit])
        for entry in entries:
            video_id = self._extract_youtube_id(entry.media.player.url)
            runtime = int(entry.media.duration.seconds)
            similar = [runtime >= int(video["runtime"]) - threshold and
                        runtime <= int(video["runtime"]) + threshold for
                        video in videos]
            if not any(similar):
                videos.append({"yt_id": video_id, "runtime":runtime})
        youtube_ids = [video['yt_id'] for video in videos]
        return youtube_ids

    def _extract_youtube_id(self, youtube_url):
        video_id = youtube_url.split('v=')[1]
        ampersand_position = video_id.find('&')
        if(ampersand_position != -1):
          video_id = video_id[0:ampersand_position]
        return video_id

    def save_to_swyftype(self):
        pass
