import sys
sys.path.append("../movie_trailers")

import boto
import os
import StringIO
import settings
import urllib2

from PIL import Image

bucket_name = 'tldw'
path = 'images/thumbnails'

def gen_s3_path(filename):
    global bucket_name
    global path

    return "http://s3.amazonaws.com/{bucket_name}/{path}/{filename}".format(
        bucket_name=bucket_name, path=path,  filename=filename)

def resize_image(url, filename):
    image = urllib2.urlopen(url).read()
    img = Image.open(StringIO.StringIO(image))

    width = 136
    wpercent = (width/float(img.size[0]))
    height = int((float(img.size[1])*float(wpercent)))
    quality_val = 95
    img = img.resize((width, height), Image.ANTIALIAS)
    img.save(filename, 'JPEG', quality=quality_val)

def upload_local_file_to_s3(filename, verbose=False):
    global bucket_name
    global path

    if verbose:
        print "uploading {filename} to amazon s3".format(filename=filename)
    
    conn = boto.connect_s3(settings.Config.AWS_ACCESS_KEY,
                           settings.Config.AWS_SECRET_KEY)
    bucket = conn.get_bucket(bucket_name)
    key_name = os.path.join(path, filename)
    key = bucket.new_key(key_name)
    key.set_contents_from_filename(filename)
    key.make_public()

def create_thumbnail(movie_title, movie_poster, verbose=False):
    filename = movie_title + '.jpg'
    resize_image(movie_poster, filename)
    upload_local_file_to_s3(filename, verbose=verbose)
    s3_path = gen_s3_path(filename)
    os.remove(filename)
    return s3_path