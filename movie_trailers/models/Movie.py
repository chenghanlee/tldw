from collections import defaultdict
from datetime import datetime
from flask.ext.mongoengine import MongoEngine
from itertools import groupby

db = MongoEngine()

class PurchaseLink(db.EmbeddedDocument):
    _ASIN = db.StringField()
    _media_type = db.StringField()
    _price = db.FloatField()
    _url = db.StringField()

    @property
    def ASIN(Self):
        return self._ASIN

    @property
    def media_type(self):
        return self._media_type

    @property
    def price(self):
        return self._price

    @property
    def url(self):
        return self._url

class Metadata(db.EmbeddedDocument):
    # various ids
    _date_added = db.DateTimeField(default=dateime.now())
    _imdb_id = db.StringField(unique=True)
    _runtime = db.IntField()

    @property
    def date_added(self):
        return self._date_added

    @property
    def imdb_id(self):
        return self._imdb_id

    @property
    def runtime(self):
        return self._runtime

class Review(db.EmbeddedDocument):
    _critic = db.StringField()
    _date = db.DateTimeField()
    _freshness = db.StringField()
    _publication = db.StringField()
    _quote = db.StringField()
    _review_link = db.StringField()

    @property
    def critic(self):
        return self._critic

    @property
    def date(self):
        return self._date

    @property
    def freshness(self):
        return self._freshness

    @property
    def publication(self):
        return self._publication

    @property
    def quote(self):
        return self._quote

    @property
    def review_link(self):
        return self._review_link


class ViewCount(db.EmbeddedDocument):
    _date = db.DateTimeField()
    _count = db.IntField()

    @property
    def date(self):
        return self._date

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        self._count = value


class Movie(db.Document, object):
    _director = db.StringField()
    _formatted_director = db.StringField()
    _title = db.StringField()
    _formatted_title = db.StringField()
    _synopsis = db.StringField()
    _critics_score = db.IntField()
    _release_date = db.DateTimeField()
    _poster = db.StringField() # full poster
    _thumbnail = db.StringField() # resized poster
    _trending_score = db.FloatField(default=0.0)

    _cast = db.ListField(db.ReferenceField('Actor'))
    _genres = db.ListField(db.StringField())
    _metadata = db.EmbeddedDocumentField(Metadata)
    _views = db.ListField(db.EmbeddedDocumentField(ViewCount))
    _reviews = db.ListField(db.EmbeddedDocumentField(Review))
    _similar_movies=db.ListField(db.StringField()) # storing imdb ids
    _trailers = db.ListField(db.StringField())
    _purchase_links=db.ListField(db.EmbeddedDocumentField(PurchaseLink))

    meta = {'indexes': ['_formatted_title', '_metadata._imdb_id', '_director', '_id',
                        '-_critics_score', '-_release_date', '-_views._date',
                        ('_genres', '-_critics_score'),
                        ('_genres', '-_release_date'),
                        ('_genres', '-_trending_score')]}

    @property
    def director(self):
        return self._director

    @property
    def title(self):
        return self._title

    @property
    def synopsis(self):
        return self._synopsis

    @property
    def critics_score(self):
        return self._critics_score

    @property
    def genres(self):
        return self._genres

    @property
    def release_date(self):
        return self._release_date

    @property
    def poster(self):
        return self._poster

    @property
    def thumbnail(self):
        return self._thumbnail

    @property
    def purchase_links(self):
        links = {link.media_type: link.url for link in self._purchase_links}
        return links

    @property
    def purchase_price(self):
        links = {link.media_type: link._price for link in self._purchase_links}
        return links

    @property
    def dvd_purchase_link(self):
        return self.purchase_links.get('DVD', None)

    @property
    def bluray_purchase_link(self):
        return self.purchase_links.get('Blu-ray', None)

    @property
    def instant_watch_purchase_link(self):
        return self.purchase_links.get('Amazon Instant Video', None)

    @property
    def cast(self, limit=6):
        return self._cast[:limit]

    @property
    def metadata(self):
        return self._metadata

    @property
    def views_by_date(self):
        return self._views

    @property
    def reviews(self):
        return self._reviews

    def normalized_reviews(self, num_total_reviews=10):
        num_fresh_reviews = max(1, int(self.critics_score
                                        / 100.0 * num_total_reviews))
        num_rotten_reviews = num_total_reviews - num_fresh_reviews

        all_reviews = defaultdict(list)
        for key, group in groupby(self.reviews, lambda review: review.freshness): 
            all_reviews[key] += [review for review in group]

        fresh_reviews = sorted(all_reviews['fresh'],
                                key= lambda review: len(review.quote),
                                reverse=True)
        rotten_reviews = sorted(all_reviews['rotten'],
                                key= lambda review: len(review.quote),
                                reverse=True)
        reviews = fresh_reviews[:num_fresh_reviews] + rotten_reviews[:num_rotten_reviews]
        return reviews

    @property
    def similar_movies(self):
        movies = Movie.objects(_metadata___imdb_id__in=self._similar_movies).only(
            "_thumbnail", "_release_date", "_title",  "_formatted_title")
        return movies

    @property
    def trailers(self):
        return self._trailers

    def trailer(self, index):
        try:
            return self._trailers[index]
        except:
            return None

    @property
    def trending_score(self):
        return self._trending_score

    @property
    def url(self):
        prefix = "/movie-trailer/"
        return prefix + self._formatted_title

    @property
    def formatted_title(self):
        return self._formatted_title


    @classmethod
    def get_movies_by_genre(cls, genre, sort):
        sort_by = {'newest': '-_release_date', 'best': '-_critics_score'
                    }.get(sort, '-_metadata._updated')
        kwargs = {} if genre == 'all' else {'_genres': genre}
        cursor = Movie.objects(**kwargs).order_by(sort_by)
        return cursor

    @classmethod
    def get_movie_by_title(cls, title):
        movie =  Movie.objects(_formatted_title=title).first()
        return movie

class Actor(db.Document):
    _name = db.StringField(unique=True)
    _biography = db.StringField(default=None)
    _headshot = db.StringField(default=None)
    _formatted_name = db.StringField(unique=True)

    _filmography = db.ListField(db.ObjectIdField(Movie))
    
    meta = {'indexes': ['_id', '_formatted_name']}
    
    @property
    def name(self):
        return self._name

    @property
    def formatted_name(self):
        return self._formatted_name

    @property
    def url(self):
        full_url = '/name/' + self.formatted_name
        return full_url

    @classmethod
    def get_actor_by_formatted_name(cls, formatted_name):
        actor = Actor.objects(_formatted_name=formatted_name).first()
        return actor

    def filmography(self, page, sort, movies_per_page=32):
        sort_by = {'newest': '-_release_date', 'best': '-_critics_score'
                    }.get(sort, '-_metadata._updated')
        cursor = Movie.objects.filter(id__in=self._filmography).order_by(sort_by)
        return cursor
            