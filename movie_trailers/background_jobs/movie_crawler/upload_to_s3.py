import sys
sys.path.append("../../")

import boto
import os
import StringIO
import settings
import urllib2

from PIL import Image

def download_image(url, filename, quality=95, width=136):
    image = urllib2.urlopen(url).read()
    image = Image.open(StringIO.StringIO(image))
    if width == "original":
        width = image.size[0]
    scale_factor = (width / float(image.size[0]))
    height = int((float(image.size[1]) * float(scale_factor)))
    image = image.resize((width, height), Image.ANTIALIAS)
    image.save(filename, 'JPEG', quality=quality)

def upload_to_s3(filename, bucket_name, path, verbose=False):
    conn = boto.connect_s3(settings.Config.AWS_ACCESS_KEY,
                            settings.Config.AWS_SECRET_KEY)
    bucket = conn.get_bucket(bucket_name)
    key_name = os.path.join(path, filename)
    key = bucket.new_key(key_name)
    key.set_contents_from_filename(filename)
    key.make_public()
    return key_name


# # need to refractor 
# def _gen_s3_path(filename):
#     global bucket_name
#     global path

#     return "http://s3.amazonaws.com/{bucket_name}/{path}/{filename}".format(
#         bucket_name=bucket_name, path=path,  filename=filename)

# # refractor to download_image(url, filename, new_width=None)
# def _resize_image(url, filename):
#     image = urllib2.urlopen(url).read()
#     img = Image.open(StringIO.StringIO(image))

#     width = 136
#     wpercent = (width/float(img.size[0]))
#     height = int((float(img.size[1])*float(wpercent)))
#     quality_val = 95
#     img = img.resize((width, height), Image.ANTIALIAS)
#     img.save(filename, 'JPEG', quality=quality_val)

# def _upload_local_file_to_s3(filename, verbose=False):
#     global bucket_name
#     global path

#     if verbose:
#         print "uploading {filename} to amazon s3".format(filename=filename)
    
#     conn = boto.connect_s3(settings.Config.AWS_ACCESS_KEY,
#                            settings.Config.AWS_SECRET_KEY)
#     bucket = conn.get_bucket(bucket_name)
#     key_name = os.path.join(path, filename)
#     key = bucket.new_key(key_name)
#     key.set_contents_from_filename(filename)
#     '''
#     CHLEE TODO:
#     Need to add a HTTP caching header to the key
#     '''
#     key.make_public()

# def create_thumbnail(movie_title, movie_poster, verbose=False):
#     filename = movie_title + '.jpg'
#     _resize_image(movie_poster, filename)
#     _upload_local_file_to_s3(filename, verbose=verbose)
#     s3_path = _gen_s3_path(filename)
#     os.remove(filename)
#     return s3_path