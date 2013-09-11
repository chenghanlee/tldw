from flask import abort, Blueprint, g, render_template
from movie_trailers.constants import genres, sorts, TTL
from movie_trailers.extensions import redis
from movie_trailers.models.Movie import Actor

actor = Blueprint("actor", __name__)

@actor.route("/name/<name>/<sort>/<int:page>")
@actor.route("/name/<name>/<sort>/")
@actor.route("/name/<name>")
def list_filmography(name, page=1, sort="newest"):
    actor = Actor.get_actor_by_url_name(name)
    if actor is None:
        abort(404)

    key = "{actor}:{sort}".format(actor=name, sort=sort)
    rv = redis.hget(key, page)
    if rv:
        return rv

    movies = actor.filmography(page, sort).only(
        "_thumbnail", "_release_date", "_title",  "_url_title")
    g.actor = actor
    g.movies = movies
    g.title = actor.name
    g.page = page
    g.possible_sorts = sorts
    g.current_sort = sort 

    rv = render_template("actor.html", g=g)
    redis.hset(key, page, rv)
    redis.expire(key, TTL)
    return rv

