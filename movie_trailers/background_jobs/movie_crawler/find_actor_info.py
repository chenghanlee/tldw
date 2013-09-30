import requests
import os

from bs4 import BeautifulSoup
from urllib import urlencode
from upload_to_s3 import download_image, upload_to_s3

def find_actor_info(name):
	query = "{name} actor".format(name=name)
	url = "http://www.bing.com/search?{query}".format(
		query=urlencode({"q": query}))
	html = _bing_search(url)
	soup = _make_soup(html)
	
	bio = _find_bio(soup)
	image_url = _find_image_url(soup)

	return {"bio": bio, "image_url": image_url}

def _bing_search(url):
	return requests.get(url).text

def _make_soup(html):
	return BeautifulSoup(html)

def _find_bio(soup):
	bio = soup.find("p", "tp_icdf")
	if bio is None:
		return None

	bio = bio.text
	if len(bio) < 50:
		return None
	else:
		return bio

def _find_image_url(soup):
	image = soup.find("div", attrs={"data-width": "110"})
	if image is None:
		return None
	
	image_url = "http://www.bing.com{src}".format(src=image['data-src'])
	image_url = image_url.replace("110", "136")
	return image_url	

# if __name__ == "__main__":
# 	info = find_actor_info("Tom Hanks")
# 	download_image(info['image_url'], 'tom-hanks.jpg', width="original")
# 	upload_to_s3("tom-hanks.jpg", "tldw", "images/actors")
# 	os.remove('tom-hanks.jpg')
