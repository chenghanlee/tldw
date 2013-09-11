from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from movie_trailers.extensions import celery, db
from movie_trailers.models.Movie import Movie
from movie_trailers.views.movie import movie
from movie_trailers.views.actor import actor


app = Flask(__name__)
app.secret_key = "e}\xe5\xbe\x9bf\x07\n\x87j\xa8\x13\x81\xef\xf7%SA\x9a\x96\xe9U\x90y"

app.register_blueprint(actor)
app.register_blueprint(movie)
app.config.from_object('movie_trailers.settings.DevConfig')
celery.config_from_object('movie_trailers.settings.CeleryConfig')    
db.init_app(app)
# DebugToolbarExtension(app)
