import urllib.request
import re

from bs4 import BeautifulSoup

# Get thumbnail from an URL
def getThumbnail(urlParam):
	url = "/".join((urlParam).split("/")[:5])
	
	websource = urllib.request.urlopen(url)
	soup = BeautifulSoup(websource.read(), "html.parser")
	image = re.search("(?P<url>https?://[^\s]+)", str(soup.find("img", {"itemprop": "image"}))).group("url")
	thumbnail = "".join(image.split('"')[:1]).replace('"','')
	
	return thumbnail

# Replace multiple substrings from a string
def replace_all(text, dic):
	for i, j in dic.items():
		text = text.replace(i, j)
	return text


# Escape special characters
def filter_name(name):
	dic = {
        "♥": "\♥",
        "♀": "\♀",
        "♂": "\♂",
        "♪": "\♪",
        "☆": "\☆"
        }

	return replace_all(name, dic)

# Check if the show's name ends with a show type and truncate it
def truncate_end_show(show):
	SHOW_TYPES = (
        '- TV',
		'- Movie',
		'- Special',
		'- OVA',
		'- ONA',
		'- Manga',
		'- Manhua',
		'- Manhwa',
		'- Novel',
		'- One-Shot',
		'- Doujinshi',
		'- Music',
		'- OEL',
		'- Unknown'
    )
    
	if show.endswith(SHOW_TYPES):
		return show[:show.rindex('-') - 1]
	return show

