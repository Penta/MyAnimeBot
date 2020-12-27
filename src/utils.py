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
		if label.upper() in ('MAL', 'MYANIMELIST', globals.SERVICE_MAL.upper()):
			return Service.MAL
		elif label.upper() in ('AL', 'ANILIST', globals.SERVICE_ANILIST.upper()):
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


def get_channels(server_id: int):
	''' Returns the registered channels for a server '''

	# TODO Make generic execute
	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute("SELECT channel FROM t_servers WHERE server = %s", [server_id])
	channels = cursor.fetchall()
	cursor.close()
	return channels


def is_server_in_db(server_id) -> bool:
	''' Checks if server is registered in the database '''

	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("SELECT server FROM t_servers WHERE server=%s", [server_id])
	data = cursor.fetchone()
	cursor.close()
	return data is not None


def get_users():
	''' Returns all registered users '''
    # Refresh database
	globals.conn.commit()

	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute('SELECT {}, service, servers FROM t_users'.format(globals.DB_USER_NAME))
	users = cursor.fetchall()
	cursor.close()
	return users
