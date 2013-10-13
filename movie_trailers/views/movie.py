import json
import movie_trailers.settings as settings

from datetime import datetime, timedelta
from flask import abort, Blueprint, g, jsonify, make_response, render_template, request
from flask.ext.mongoengine import Pagination
from movie_trailers.background_jobs.movie_stats.movie_stats import inc_view_count
from movie_trailers.constants import genres, sorts, TTL
from movie_trailers.extensions import redis
from movie_trailers.models.Movie import Movie
from swiftype import swiftype

movie = Blueprint("movie", __name__)

@movie.after_request
def set_http_header(response):
    max_age = 3600 # 1 hour
    minutes = 60 # 1 hour 
    expires = datetime.utcnow() + timedelta(minutes=minutes)
    expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
    response.headers['Cache-Control'] = "public, max-age={max_age}".format(
        max_age=max_age)
    response.headers['Expires'] = expires
    return response

@movie.route("/search", methods=["POST"])
def search(per_page=10):
    USERNAME = settings.Config.SW_EMAIL
    PASSWORD = settings.Config.SW_PASSWORD
    API_KEY = settings.Config.SW_API_KEY
    SW_ENGINE_SLUG = settings.Config.SW_ENGINE_SLUG
    search_term = request.form.get('search')
    client = swiftype.Client(username=USERNAME, password=PASSWORD,
                api_key=API_KEY)

    results = client.search(SW_ENGINE_SLUG, search_term, 
                options={"search_fields": {"trailer": ["title"]}})
    results = [result for result in results['body']['records']['trailer']][:per_page]
    g.results = [{"thumbnail": result.get("picture"), "genres": result.get("genres"),
                  "title": result.get("title"), "url": result.get("url"), 
                  "release_year": str(result.get("release_date")).split("-")[0],
                  "cast": result.get("cast"), "synopsis": result.get("synopsis")}
                  for result in results]
    g.search_term = search_term

    return render_template("search.html")

@movie.route("/genre/<genre>/<sort>/<int:page>", methods=["GET"])
@movie.route("/genre/<genre>/<sort>", methods=["GET"])
@movie.route("/genre/<genre>/", methods=["GET"])
@movie.route("/", methods=["GET"])
def list_movie_by_genre_get(genre="all", page=1, sort="newest", per_page=32):
    key = "genre:{genre}:{sort}".format(genre=genre, page=page, sort=sort)
    rv = redis.hget(key, page)
    if rv:
        return rv

    if page < 1:
        return abort(404)

    if sort not in ["newest", "popular", "best"]:
        return abort(404)

    cursor = Movie.get_movies_by_genre(genre, sort).only(
                "_critics_score", "_thumbnail", "_release_date", "_title",  "_formatted_title")
    paginated_movies = Pagination(cursor, page, per_page)
    movies = [movie for movie in paginated_movies.items]

    # setting up the request context and passing some information into the template
    g.has_next = paginated_movies.has_next
    g.has_prev = paginated_movies.has_prev
    g.possible_genres = genres
    g.possible_sorts = sorts
    g.current_genre = genre
    g.current_sort = sort
    g.movies = movies
    g.page = page
    g.title = genre
    rv = render_template("genre.html", g=g)

    redis.hset(key, page, rv)
    redis.expire(key, TTL)
    return rv

@movie.route("/movie-trailer/<movie_name>/<int:index>", methods=["GET"])
@movie.route("/movie-trailer/<movie_name>/", methods=["GET"])
@movie.route("/movie-trailer/<movie_name>", methods=["GET"])
def show_trailer(movie_name, index=1):
    movie = Movie.get_movie_by_title(movie_name)
    if movie is None:
        return abort(404)
    
    key = "movie-trailer:{name}".format(name=movie_name, index=index)
    rv = redis.hget(key, index)
    if rv:
        return rv

    trailer = movie.trailer(index-1)
    youtube_id = trailer if trailer else None
    reviews = movie.normalized_reviews()
    middle = len(reviews)/2
    reviews_in_left_column = reviews[0::2]
    reviews_in_right_column = reviews[1::2]
    one_click_purchase_link = movie.purchase_links.get("Amazon Instant Video") or \
                              movie.purchase_links.get("DVD") or \
                              movie.purchase_links.get("Blu-ray") 
    rv = render_template("trailer.html", movie=movie, current_index=index,
                            youtube_id=youtube_id, reviews=reviews, 
                            reviews_in_left_column=reviews_in_left_column,
                            reviews_in_right_column=reviews_in_right_column,
                            one_click_purchase_link=one_click_purchase_link)
    inc_view_count.delay(formatted_title=movie_name)
    redis.hset(key, index, rv)
    redis.expire(key, TTL)
    return rv

@movie.route("/movie-trailer/<movie_name>/<int:index>", methods=["POST"])
def return_youtube_id(movie_name, index=1):
    movie = Movie.get_movie_by_title(movie_name)
    if movie is None:
        return None

    key = "youtube:{name}".format(name=movie_name)
    rv = redis.hget(key, page)
    if rv:
        return jsonify(youtubeID=rv)

    trailer = movie.trailer(index-1)
    if trailer:
        youtube_id = trailer.youtube_id
    else:
        youtube_id = None

    rv = jsonify(youtubeID=youtube_id)
    redis_set(key, page, rv)
    redis.expire(key, TTL)
    return rv