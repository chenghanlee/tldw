import json

from flask import abort, Blueprint, g, jsonify, render_template, request
from flask.ext.mongoengine import Pagination
from movie_trailers.async import inc_view_count
from movie_trailers.constants import genres, sorts
from movie_trailers.extensions import redis
from movie_trailers.models.Movie import Actor, Movie

movie = Blueprint("movie", __name__)

# @movie.route("/genre/all", methods=["GET"])
# @movie.route("/", methods=["GET"])
# def show_all_movies():
#     page = int(request.args.get("page", 0))
#     sort = request.args.get("sort", "newest")
    
#     key = "genre:all:{sort}".format(page=page, sort=sort)
#     rv = redis.hget(key, page)
#     if rv:
#         return rv
    
#     movies = Movie.get_movies_by_genre("all", page, sort)
    
#     rv = render_template("gallery.html", movies=movies)
#     redis.hset(key, page, rv)
#     redis.expire(key, 7200)
#     return rv

@movie.route("/genre/<genre>/<sort>/<int:page>", methods=["GET"])
@movie.route("/genre/<genre>/<sort>", methods=["GET"])
@movie.route("/genre/<genre>/", methods=["GET"])
@movie.route("/", methods=["GET"])
def list_movie_by_genre_get(genre="all", page=1, sort="newest", per_page=32):
    # key = "genre:{genre}:{sort}:get".format(genre=genre, page=page, sort=sort)
    # rv = redis.hget(key, page)
    # if rv:
    #     return rv

    if page < 1:
        return abort(404)

    if sort not in ["newest", 'popular', 'best']:
        return abort(404)

    cursor = Movie.get_movies_by_genre(genre, sort).only(
                "_critic_rating", "_poster", "_release_date", "_title",  "_url_title")
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
    # redis.hset(key, page, rv)
    # redis.expire(key, 7200)
    return rv

# @movie.route("/genre/<genre>/<sort>", methods=["POST"])
# @movie.route("/genre/<genre>/", methods=["POSt"])
# @movie.route("/", methods=["POST"])
# def list_movie_by_genre_post(genre="all", sort="newest"):
#     # CHLEE TODO:
#     # 2) come up with a better name for the key
    
#     try:
#         start_index = int(request.form.get("index"))
#         start_index = start_index + 1
#     except:
#         return jsonify(status="error", msg="start index is not an int")
   
#     # key = "genre:{genre}:{sort}:post".format(genre=genre, page=page, sort=sort)
#     # rv = redis.hget(key, page)
#     # if rv:
#     #     return rv
    
#     cursor = Movie.get_movies_by_genre(
#                 genre, start_index, sort, movies_per_page=16).only("_title", "_thumbnail", "_url_title")

#     movies = {"movies":
#                 [{"index": start_index + index,
#                     "poster": movie.poster,
#                     "title": movie.title, 
#                     "url": "/movie-trailer/{name}".format(name=movie.url_title)
#                  } for index, movie in enumerate(cursor)]}
#     rv = movies

#     # redis.hset(key, page, rv)
#     # redis.expire(key, 7200)

#     return jsonify(status="success", data=movies)

@movie.route("/movie-trailer/<movie_name>/<int:index>", methods=["GET"])
@movie.route("/movie-trailer/<movie_name>/", methods=["GET"])
@movie.route("/movie-trailer/<movie_name>", methods=["GET"])
def show_trailer(movie_name, index=1):
    movie = Movie.get_movie_by_title(movie_name)
    if movie is None:
        return abort(404)
    
    # key = "movie-trailer:{name}".format(name=movie_name, index=index)
    # rv = redis.hget(key, index)
    # if rv:
    #     return rv
    trailer = movie.trailer(index-1)
    youtube_id = trailer.youtube_id if trailer else None
    reviews = movie.normalized_reviews()
    middle = len(reviews)/2
    reviews_in_left_column = reviews[0::2]
    reviews_in_right_column = reviews[1::2]
    rv = render_template("trailer.html", movie=movie, current_index=index,
                            youtube_id=youtube_id, reviews=reviews, 
                            reviews_in_left_column=reviews_in_left_column,
                            reviews_in_right_column=reviews_in_right_column)
    inc_view_count.delay(url_title=movie_name)
    # redis.hset(key, index, rv)
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
    return rv


@movie.route("/name/<name>/<sort>/<int:page>")
@movie.route("/name/<name>/<sort>/")
@movie.route("/name/<name>")
def list_filmography(name, page=1, sort="newest"):
    actor = Actor.get_actor_by_url_name(name)
    if actor is None:
        abort(404)

    # key = "{actor}:{sort}".format(actor=name, sort=sort)
    # rv = redis.hget(key, page)
    # if rv:
    #     return rv
    movies = actor.filmography(page, sort).only(
                "_poster", "_release_date", "_title",  "_url_title")
    g.actor = actor
    g.movies = movies
    g.title = actor.name
    g.page = page
    g.possible_sorts = sorts
    g.current_sort = sort 

    rv = render_template("actor.html", g=g)
    # redis.hset(key, page, rv)
    return rv

