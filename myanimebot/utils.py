import datetime
import re
import urllib.request
from enum import Enum
from typing import List

from bs4 import BeautifulSoup

import myanimebot.globals as globals

class Service(Enum):
	MAL=globals.SERVICE_MAL
	ANILIST=globals.SERVICE_ANILIST

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


def replace_all(text : str, replace_dic : dict) -> str:
	''' Replace multiple substrings from a string '''
	
	for replace_key, replace_value in replace_dic.items():
		text = text.replace(replace_key, replace_value)
	return text


def filter_name(name : str) -> str:
	''' Escapes special characters from name '''

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
	show_types = (
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
    
	for show_type in show_types:
		if show.endswith(show_type):
			new_show = show[:-len(show_type)]
			# Check if space at the end
			if new_show.endswith(' '):
				new_show = new_show[:-1]
			return new_show
	return show


def get_channels(server_id: int) -> dict:
	''' Returns the registered channels for a server '''

	if server_id is None:
		return None

	# TODO Make generic execute
	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute("SELECT channel FROM t_servers WHERE server = %s", [server_id])
	channels = cursor.fetchall()
	cursor.close()
	return channels


def is_server_in_db(server_id : str) -> bool:
	''' Checks if server is registered in the database '''

	if server_id is None:
		return False

	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("SELECT server FROM t_servers WHERE server=%s", [server_id])
	data = cursor.fetchone()
	cursor.close()
	return data is not None


def get_users() -> List[dict]:
	''' Returns all registered users '''

	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute('SELECT {}, service, servers FROM t_users'.format(globals.DB_USER_NAME))
	users = cursor.fetchall()
	cursor.close()
	return users

def get_user_servers(user_name : str, service : Service) -> str:
	''' Returns a list of every registered servers for a user of a specific service, as a string '''

	if user_name is None or service is None:
		return

	cursor = globals.conn.cursor(buffered=True, dictionary=True)
	cursor.execute("SELECT servers FROM t_users WHERE LOWER({})=%s AND service=%s".format(globals.DB_USER_NAME),
					 [user_name.lower(), service.value])
	user_servers = cursor.fetchone()
	cursor.close()

	if user_servers is not None:
		return user_servers["servers"]
	return None


def remove_server_from_servers(server : str, servers : str) -> str:
	''' Removes the server from a comma-separated string containing multiple servers '''

	servers_list = servers.split(',')

	# If the server is not found, return None
	if server not in servers_list:
		return None

	# Remove every occurence of server
	servers_list = [x for x in servers_list if x != server]
	# Build server-free string
	return ','.join(servers_list)


def delete_user_from_db(user_name : str, service : Service) -> bool:
	''' Removes the user from the database '''

	if user_name is None or service is None:
		globals.logger.warning("Error while trying to delete user '{}' with service '{}'".format(user_name, service))
		return False

	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("DELETE FROM t_users WHERE LOWER({}) = %s AND service=%s".format(globals.DB_USER_NAME),
						 [user_name.lower(), service.value])
	globals.conn.commit()
	cursor.close()
	return True


def update_user_servers_db(user_name : str, service : Service, servers : str) -> bool:
	if user_name is None or service is None or servers is None:
		globals.logger.warning("Error while trying to update user's servers. User '{}' with service '{}' and servers '{}'".format(user_name, service, servers))
		return False

	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("UPDATE t_users SET servers = %s WHERE LOWER({}) = %s AND service=%s".format(globals.DB_USER_NAME),
	 					 [servers, user_name.lower(), service.value])
	globals.conn.commit()
	cursor.close()
	return True


def insert_user_into_db(user_name : str, service : Service, servers : str) -> bool:
	''' Add the user to the database '''

	if user_name is None or service is None or servers is None:
		globals.logger.warning("Error while trying to add user '{}' with service '{}' and servers '{}'".format(user_name, service, servers))
		return False

	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("INSERT INTO t_users ({}, service, servers) VALUES (%s, %s, %s)".format(globals.DB_USER_NAME),
						[user_name, service.value, servers])
	globals.conn.commit()
	cursor.close()
	return True
