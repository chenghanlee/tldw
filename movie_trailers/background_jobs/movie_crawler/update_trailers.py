import sys
sys.path.append("../../../movie_trailers")
sys.path.append("../../../movie_trailers/models")

from Movie import db, Movie, Actor

import fuzzywuzzy.fuzz
import gdata.youtube
import gdata.youtube.service
import settings

db_conn_settings = dict([(k.lower(), v) for k, v in
                    settings.ProdConfig.MONGODB_SETTINGS.items() if v])
db.connect(**db_conn_settings)


        
def remove_duplicate_youtube_videos(entries, threshold=10):
    '''
    This method removes duplicate videos by measuring the runtime
    of the youtube videos.

    If two videos are within 5 seconds (the threshold) of each
    other in runtime,  we assume that one of the videos is a duplicate
    of the other.
    '''
    videos = []
    for entry in entries:
        runtime = int(entry.media.duration.seconds)
        similar = [runtime >= int(video["runtime"]) - threshold and
                   runtime <= int(video["runtime"]) + threshold for
                   video in videos]
        if not any(similar):
            print entry.media.title.text
            video_id = extract_youtube_id(entry.media.player.url)
            videos.append({"yt_id": video_id, "runtime": runtime})
    yt_ids = [video['yt_id'] for video in videos]
    return yt_ids

def remove_long_youtube_videos(entries, max_seconds=600):
    entries = filter(lambda entry:
                int(entry.media.duration.seconds) < max_seconds,
                entries)
    return entries

def remove_unrelated_videos(title, entries):
    entries = filter(lambda entry:
                        fuzzywuzzy.fuzz.ratio(entry.media.title.text.decode('utf-8').lower(), title.lower()) > 20,
                        entries)
    return entries

def extract_youtube_id(youtube_url):
    video_id = youtube_url.split('v=')[1]
    ampersand_position = video_id.find('&')
    if(ampersand_position != -1):
      video_id = video_id[0:ampersand_position]

    return video_id
    
def trailers(movie, limit=3):
    '''
    This function returns a list of trailers for this movie.
    
    We will use TMDB's data if it returns  3 or more trailers. If not,
    we will query youtube with the search term: "{movie_name} trailer
    {release_year}" to find trailers for this movie.

    Returns a list of youtube ids of the trailers
    '''
    release_year = str(movie.release_date).split('-')[0]
    query = gdata.youtube.service.YouTubeVideoQuery()
    query.vq = "{title} trailer {release_year} ".format(
                    title=movie.title, release_year=release_year)
    query.orderby = 'relevance'

    yt_service = gdata.youtube.service.YouTubeService()
    feed = yt_service.YouTubeQuery(query)
    entries = remove_long_youtube_videos(feed.entry[:3])
    entries = remove_unrelated_videos(movie.title, entries)
    print len(entries)
    unique_entries = remove_duplicate_youtube_videos(entries)
    return unique_entries

if __name__ == "__main__":
    movies = Movie.objects.timeout(False)
    for index, movie in enumerate(movies):
        print movie.title

        movie._trailers = trailers(movie)
        print movie._trailers
        movie.save()

