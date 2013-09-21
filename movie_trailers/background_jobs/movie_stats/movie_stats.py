from celery import Celery
from celery.contrib.batches import Batches
from collections import defaultdict
from datetime import datetime
from movie_trailers import settings
from movie_trailers.constants import reference_date
from movie_trailers.models.Movie import Movie, ViewCount

celery = Celery('movie_trailers.async')
celery.config_from_object(settings.CeleryConfig)

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
        formatted_title = request.kwargs['formatted_title']
        views[formatted_title] += 1

    for formatted_title, num_views in views.iteritems():
        movie = Movie.objects(_formatted_title=formatted_title).first()
        view = filter(lambda x: datetime.date(x.date) == today,
                         movie.views_by_date)
        if len(view) > 0:
            view[0]._count = view[0]._count + num_views
            movie.save()
        else:
            new_view = ViewCount(_date=today, _count=num_views)
            movie.update(push___views=new_view)
