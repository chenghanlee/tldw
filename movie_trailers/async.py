#HACK: so that celery worker now works
import sys
sys.path.append("..")

from celery.contrib.batches import Batches
from collections import defaultdict
from datetime import datetime
from movie_trailers.constants import reference_date
from movie_trailers.extensions import celery
from movie_trailers.models.Movie import Movie, ViewCount


@celery.task(base=Batches, flush_interval=120, queue="movie_stats")
def inc_view_count(requests):
    '''
    This is a celery job that batch the number of views for a
    movie trailer page

    This job will run once every hour.
    '''
    views = defaultdict(int)
    today = datetime.date(datetime.now())

    for request in requests:
        url_title = request.kwargs['url_title']
        views[url_title] += 1

    for url_title, num_views in views.iteritems():
        movie = Movie.objects(_url_title=url_title).first()
        view = filter(lambda x: datetime.date(x.date) == today,
                         movie.views_by_date)
        if len(view) > 0:
            view[0]._count = view[0]._count + num_views
            movie.save()
        else:
            new_view = ViewCount(_date=today, _count=num_views)
            movie.update(push___views=new_view)
