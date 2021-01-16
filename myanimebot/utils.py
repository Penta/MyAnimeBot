import datetime
from enum import Enum
from typing import List

import myanimebot.globals as globals


# TODO Redo all of the desc/status system

# Media Status colors
CURRENT_COLOR     = "0x00FF00"
PLANNING_COLOR    = "0xBFBFBF"
COMPLETED_COLOR   = "0c0000FF"
DROPPED_COLOR     = "0xFF0000"
PAUSED_COLOR      = "0xFFFF00"
REPEATING_COLOR   = "0x008000"


class Service(Enum):
    MAL=globals.SERVICE_MAL
    ANILIST=globals.SERVICE_ANILIST

    @staticmethod
    def from_str(label: str):
        if label is None: raise TypeError

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
        if label is None: raise TypeError

        if label.upper() in ('ANIME', 'ANIME_LIST'):
            return MediaType.ANIME
        elif label.upper() in ('MANGA', 'MANGA_LIST'):
            return MediaType.MANGA
        else:
            raise NotImplementedError('Error: Cannot convert "{}" to a MediaType'.format(label))


    def get_media_count_type(self):
        if self == MediaType.ANIME:
            return 'episodes'
        elif self == MediaType.MANGA:
            return 'chapters'
        else:
            raise NotImplementedError('Unknown MediaType "{}"'.format(self))


class MediaStatus(Enum):
    CURRENT     = CURRENT_COLOR
    PLANNING    = PLANNING_COLOR
    COMPLETED   = COMPLETED_COLOR
    DROPPED     = DROPPED_COLOR
    PAUSED      = PAUSED_COLOR
    REPEATING   = REPEATING_COLOR

    @staticmethod
    def from_str(label: str):
        if label is None: raise TypeError

        first_word = label.split(' ')[0].upper()

        if first_word in ['READ', 'READING', 'WATCHED', 'WATCHING']:
            return MediaStatus.CURRENT
        elif first_word in ['PLANS', 'PLAN']:
            return MediaStatus.PLANNING
        elif first_word in ['COMPLETED']:
            return MediaStatus.COMPLETED
        elif first_word in ['DROPPED']:
            return MediaStatus.DROPPED
        elif first_word in ['PAUSED', 'ON-HOLD']:
            return MediaStatus.PAUSED
        elif first_word in ['REREAD', 'REREADING', 'REWATCHED', 'REWATCHING', 'RE-READING', 'RE-WATCHING', 'RE-READ', 'RE-WATCHED']:
            return MediaStatus.REPEATING
        else:
            raise NotImplementedError('Error: Cannot convert "{}" to a MediaStatus'.format(label))


class User():
    data = None

    def __init__(self,
                  id            : int,
                  service_id    : int,
                  name          : str,
                  servers       : List[int]):
        self.id = id
        self.service_id = service_id
        self.name = name
        self.servers = servers

class Media():
    def __init__(self,
                 name       : str,
                 url        : str,
                 episodes   : str,
                 image      : str,
                 type       : MediaType):
        self.name = name
        self.url = url
        self.episodes = episodes
        self.image = image
        self.type = type


class Feed():
    def __init__(self,
                 service        : Service,
                 date_publication : datetime.datetime,
                 user           : User,
                 status         : MediaStatus,
                 description    : str, # TODO Need to change
                 progress       : str,
                 media          : Media
                 ):
        self.service = service
        self.date_publication = date_publication
        self.user = user
        self.status = status
        self.media = media
        self.description = description
        self.progress = progress

    
    def get_status_str(self):

        if self.status == MediaStatus.CURRENT \
        or self.status == MediaStatus.REPEATING:

            if self.media.type == MediaType.ANIME:
                status_str = 'Watching'
            elif self.media.type == MediaType.MANGA:
                status_str = 'Reading'
            else:
                raise NotImplementedError('Unknown MediaType: {}'.format(self.media.type))

            # Add prefix if rewatching
            if self.status == MediaStatus.REPEATING:
                status_str = 'Re-{}'.format(status_str.lower())

        elif self.status == MediaStatus.COMPLETED:
            status_str = 'Completed'
        elif self.status == MediaStatus.PAUSED:
            status_str = 'Paused'
        elif self.status == MediaStatus.DROPPED:
            status_str = 'Dropped'
        elif self.status == MediaStatus.PLANNING:

            if self.media.type == MediaType.ANIME:
                media_type_label = 'watch'
            elif self.media.type == MediaType.MANGA:
                media_type_label = 'read'
            else:
                raise NotImplementedError('Unknown MediaType: {}'.format(self.media.type))

            status_str = 'Plans to {}'.format(media_type_label)
        else:
            raise NotImplementedError('Unknown MediaStatus: {}'.format(self.status))

        return status_str


def replace_all(text : str, replace_dic : dict) -> str:
    '''Replace multiple substrings from a string'''
    
    if text is None or replace_dic is None:
        return text

    for replace_key, replace_value in replace_dic.items():
        text = text.replace(replace_key, replace_value)
    return text


def filter_name(name : str) -> str:
    '''Escapes special characters from name'''

    dic = {
        "♥": "\♥",
        "♀": "\♀",
        "♂": "\♂",
        "♪": "\♪",
        "☆": "\☆"
        }

    return replace_all(name, dic)

# Check if the show's name ends with a show type and truncate it
def truncate_end_show(media_name : str):
    '''Check if a show's name ends with a show type and truncate it'''

    if media_name is None: return None

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
        '- Unknown',
        '- Light Novel'
    )

    for show_type in show_types:
        if media_name.endswith(show_type):
            new_show = media_name[:-len(show_type)]
            # Check if space at the end
            if new_show.endswith(' '):
                new_show = new_show[:-1]
            return new_show
    return media_name


def build_description_string(feed : Feed):
    '''Build and returns a string describing the feed'''

    media_type_count = feed.media.type.get_media_count_type()
    status_str = feed.get_status_str()

    # Build the string
    return '{} | {} of {} {}'.format(status_str, feed.progress, feed.media.episodes, media_type_count)


def get_channels(server_id: int) -> dict:
    '''Returns the registered channels for a server'''

    if server_id is None: return None

    # TODO Make generic execute
    cursor = globals.conn.cursor(buffered=True, dictionary=True)
    cursor.execute("SELECT channel FROM t_servers WHERE server = %s", [server_id])
    channels = cursor.fetchall()
    cursor.close()
    return channels


def is_server_in_db(server_id : str) -> bool:
    '''Checks if server is registered in the database'''

    if server_id is None:
        return False

    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("SELECT server FROM t_servers WHERE server=%s", [server_id])
    data = cursor.fetchone()
    cursor.close()
    return data is not None


def get_users() -> List[dict]:
    '''Returns all registered users'''

    cursor = globals.conn.cursor(buffered=True, dictionary=True)
    cursor.execute('SELECT {}, service, servers FROM t_users'.format(globals.DB_USER_NAME))
    users = cursor.fetchall()
    cursor.close()
    return users

def get_user_servers(user_name : str, service : Service) -> str:
    '''Returns a list of every registered servers for a user of a specific service, as a string'''

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
    '''Removes the server from a comma-separated string containing multiple servers'''

    servers_list = servers.split(',')

    # If the server is not found, return None
    if server not in servers_list:
        return None

    # Remove every occurence of server
    servers_list = [x for x in servers_list if x != server]
    # Build server-free string
    return ','.join(servers_list)


def delete_user_from_db(user_name : str, service : Service) -> bool:
    '''Removes the user from the database'''

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
    '''Add the user to the database'''

    if user_name is None or service is None or servers is None:
        globals.logger.warning("Error while trying to add user '{}' with service '{}' and servers '{}'".format(user_name, service, servers))
        return False

    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("INSERT INTO t_users ({}, service, servers) VALUES (%s, %s, %s)".format(globals.DB_USER_NAME),
                        [user_name, service.value, servers])
    globals.conn.commit()
    cursor.close()
    return True

def get_allowed_role(server : int) -> int:
    '''Return the allowed role for a given server'''
    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("SELECT admin_group FROM t_servers WHERE server=%s LIMIT 1", [str(server)])
    allowedRole = cursor.fetchone()
    cursor.close()

    return allowedRole[0]