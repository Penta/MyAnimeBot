import urllib.request
import re
import datetime
from typing import List
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


class MediaType(Enum):
    ANIME="ANIME"
    MANGA="MANGA"

    @staticmethod
    def from_str(label: str):
        if label.upper() in ('ANIME', 'ANIME_LIST'):
            return MediaType.ANIME
        elif label.upper() in ('MANGA', 'MANGA_LIST'):
            return MediaType.MANGA
        else:
            raise NotImplementedError('Error: Cannot convert "{}" to a MediaType'.format(label))


class User():
	data = None

	def __init__(self,
				  id			: int,
				  service_id	: int,
				  name			: str,
				  servers		: List[int]):
		self.id = id
		self.service_id = service_id
		self.name = name
		self.servers = servers

class Media():
	def __init__(self,
				 name		: str,
				 url		: str,
				 episodes	: str,
				 image		: str,
				 type		: MediaType):
		self.name = name
		self.url = url
		self.episodes = episodes
		self.image = image
		self.type = type

	@staticmethod
	def get_number_episodes(activity):
		media_type = MediaType.from_str(activity["type"])
		episodes = '?'
		if media_type == MediaType.ANIME:
			episodes = activity["media"]["episodes"]
		elif media_type == MediaType.MANGA:
			episodes = activity["media"]["chapters"]
		else:
			raise NotImplementedError('Error: Unknown media type "{}"'.format(media_type))
		if episodes is None:
			episodes = '?'
		return episodes


class Feed():
	def __init__(self,
				 service 		: Service,
				 date_publication : datetime.datetime,
				 user 			: User,
				 status			: str, # TODO Need to change
				 description	: str, # TODO Need to change
				 media 			: Media
				 ):
		self.service = service
		self.date_publication = date_publication
		self.user = user
		self.status = status
		self.media = media
		self.description = description


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
	# globals.conn.commit()

	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute('SELECT {}, service, servers FROM t_users'.format(globals.DB_USER_NAME))
	users = cursor.fetchall()
	cursor.close()
	return users


def get_user(user_id):
	''' Returns the user from an id '''
    # Refresh database
	# globals.conn.commit()

	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute('SELECT {}, service, servers FROM t_users WHERE '.format(globals.DB_USER_NAME))
	users = cursor.fetchall()
	cursor.close()
	return users
