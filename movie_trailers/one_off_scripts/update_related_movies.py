import sys
sys.path.append("../../movie_trailers")
sys.path.append("../../movie_trailers/models")
sys.path.append("../../movie_trailers/background_jobs/movie_crawler")

import json
import mechanize
import settings
import time

from bs4 import BeautifulSoup
from Movie import db, Movie
from movie_crawler import save_movie_info_to_mongo
from rottentomatoes import RT

if __name__ == "__main__":
    db_conn_settings = dict([(k.lower(), v) for k, v in
        settings.ProdConfig.MONGODB_SETTINGS.items() if v])
    db.connect(**db_conn_settings)
    
    rotten_tomatoe_api_key = settings.Config.ROTTEN_TOMATOES_API_KEY
    rt = RT(rotten_tomatoe_api_key)        
    movies = Movie.objects.timeout(False)
    for index, movie in enumerate(movies):
        print index
        if len(movie.similar_movies) == 0:
            print "updating: %s %s" % (movie.title, movie.release_date)

            # creating our search term
            search_term = movie.title.replace(" ", "+")
            url = "https://www.google.com/search?q=%s+Movie" % search_term

            # querying google
            br = mechanize.Browser()
            br.addheaders = [('user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.69 Safari/537.36'),
            ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
            br.set_handle_robots(False)
            br.open(url)

            # making soup
            html = br.response().read()
            soup = BeautifulSoup(html)
            related_movies = soup.find_all("a", "vrt_tl")
            if len(related_movies) == 10:
                related_movies = related_movies[5:]
            related_movies = [related_movie.text for related_movie in related_movies]
            print str(related_movies)

            # find imdb of related movie
            # movie to rotten tomatoes if not previous saved
            imdb_ids = []   
            for related_movie in related_movies:
                try:
                    movie_info = rt.search(related_movie)[0]
                    rt_id = movie_info['id']
                    imdb_id = "tt" + movie_info['alternate_ids']['imdb']
                    imdb_ids.append(imdb_id)
                    save_movie_info_to_mongo.delay(related_movie, rt_id=rt_id)
                except Exception as e:
                    print e
                    continue

            # saving the imdb ids
            if len(imdb_ids) > 0:
                print imdb_ids
                movie._similar_movies = imdb_ids
                movie.save()
            time.sleep(5)



    # search_term = "Little Miss Sunshine".replace(" ", "+")
    # url = "https://www.google.com/search?q=%s+Movie" % search_term

    # # querying google
    # br = mechanize.Browser()
    # br.addheaders = [('user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.69 Safari/537.36'),
    # ('accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')]
    # br.set_handle_robots(False)
    # br.open(url)

    # # making soup
    # html = br.response().read()
    # soup = BeautifulSoup(html)
    # related_movies = soup.find_all("a", "vrt_tl")
    # related_movies = [movie.text for movie in related_movies]
    # print len(related_movies)
    # print str(related_movies)