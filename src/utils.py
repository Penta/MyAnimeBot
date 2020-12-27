import urllib.request
import re
from enum import Enum

from bs4 import BeautifulSoup

import globals


class Service(Enum):
	MAL="MyAnimeList"
	ANILIST="AniList"

	@staticmethod
	def from_str(label: str):
		if label.upper() in ('MAL', 'MYANIMELIST', globals.SERVICE_MAL):
			return Service.MAL
		elif label.upper() in ('AL', 'ANILIST', globals.SERVICE_ANILIST):
			return Service.ANILIST
		else:
			raise NotImplementedError('Error: Cannot convert "{}" to a Service'.format(label))


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


def get_user_data():
    ''' Returns the user's data store in the database table t_users '''

    try:
        db_user = globals.conn.cursor(buffered=True, dictionary=True)
        db_user.execute("SELECT mal_user, servers FROM t_users")
        return db_user.fetchone()
    except Exception as e:
        # TODO Catch exception
        globals.logger.critical("Database unavailable! ({})".format(e))
        quit()


def get_channels(server):
	''' Returns the registered channels for a server '''

	# TODO Make generic execute
	db_srv = globals.conn.cursor(buffered=True, dictionary=True)
	db_srv.execute("SELECT channel FROM t_servers WHERE server = %s", [server])
	return db_srv.fetchall()
