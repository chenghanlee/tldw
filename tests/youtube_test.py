import gdata.youtube
import gdata.youtube.service


def _remove_duplicate_yt_videos(feed, limit, threshold=5):
    '''
    This method removes duplicate videos by measuring the runtime
    of the videos in feed.

    If two videos are within 5 seconds of each other in runtime, 
    we assume that one of the videos is a duplicate of the other.
    '''
    videos = []
    for entry in feed.entry[:limit]:
        print int(runtime)
        not_similar = [runtime < int(video["runtime"]) - threshold or
                       runtime > int(video["runtime"]) + threshold for
                       video in videos]
        if all(not_similar):
            videos.append({"yt_id": video_id, "runtime":runtime})
    youtube_ids = [video['yt_id'] for video in videos]
    return youtube_ids


if __name__ == "__main__":
    yt_service = gdata.youtube.service.YouTubeService()
    query = gdata.youtube.service.YouTubeVideoQuery()
    query.vq = "{title} trailer {release_year} ".format(
                    title="toy story 3", release_year="2010")
    query.orderby = 'relevance'
    feed = yt_service.YouTubeQuery(query)
    print _remove_duplicate_yt_videos(feed, 3)