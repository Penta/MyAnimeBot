import requests
import time
import datetime
from enum import Enum

import globals
import myanimebot
import utils

ANILIST_GRAPHQL_URL = 'https://graphql.anilist.co'

DEBUG_USERS = [
    102213, # lululekiddo
    151824  # Pentou
]

DEBUG_USERS_NAME = [
    "lululekiddo",
    "Pentou"
]

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


class MediaListStatus(Enum):
    CURRENT=0
    PLANNING=1
    COMPLETED=2
    DROPPED=3
    PAUSED=4
    REPEATING=5

    @staticmethod
    def from_str(label: str):
        if label.upper().startswith('READ') or \
            label.upper().startswith('WATCHED') :
            return MediaListStatus.CURRENT
        elif label.upper().startswith('PLANS'):
            return MediaListStatus.PLANNING
        elif label.upper().startswith('COMPLETED'):
            return MediaListStatus.COMPLETED
        elif label.upper().startswith('DROPPED'):
            return MediaListStatus.DROPPED
        elif label.upper().startswith('PAUSED'):
            return MediaListStatus.PAUSED
        elif label.upper().startswith('REREAD') or \
              label.upper().startswith('REWATCHED'):
            return MediaListStatus.REPEATING
        else:
            raise NotImplementedError('Error: Cannot convert "{}" to a MediaListStatus'.format(label))


def get_mal_id_from_anilist_id(anilist_media_id, media_type: MediaType):
    """ Converts an AniList media ID to a MyAnimeList ID and returns it """

    query = '''query($id: Int, $type: MediaType){
        Media(id: $id, type: $type) {
            idMal
        }
    }'''

    variables = {
        'id': anilist_media_id,
        'type': media_type.value
    }

    try:
        response = requests.post(ANILIST_GRAPHQL_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        return response.json()["data"]["Media"]["idMal"]
    except requests.HTTPError as e:
        #TODO Correct error response
        print('ERROR WRONG RESPONSE CODE')
    except Exception as e:
        #TODO Correct error response
        print('UNKNOWN Error when trying to get mal id :')
        print(e)
    return None

def get_thumbnail_from_anilist_id(anilist_media_id, media_type: MediaType):
    """ Returns the MAL thumbnail from an AniList media ID """

    # TODO Catch exception or if is None
    print("Trying to get MAL ID from AniList ID {}".format(anilist_media_id))
    mal_id = get_mal_id_from_anilist_id(anilist_media_id, media_type)
    print("Got MAL ID {} from AniList ID {}".format(mal_id, anilist_media_id))

    # Building MyAnimeList URL
    mal_url = globals.MAL_URL
    if media_type == MediaType.ANIME:
        mal_url += "anime/"
    elif media_type == MediaType.MANGA:
        mal_url += "manga/"
    else:
        raise Exception("Error when getting thumbnail from AniList ID {} : Unknown Mediatype {}".format(anilist_media_id, media_type))
    mal_url += str(mal_id)

    print("Getting thumbnail from URL '{}'".format(mal_url))
    return utils.getThumbnail(mal_url)
    

def get_anilist_userId_from_name(user_name : str):
    """ Searches an AniList user by its name and returns its ID """

    query = '''query($userName: String){
        User(name: $userName) {
            id
        }
    }'''

    variables = {
        'userName': user_name
    }

    try:
        response = requests.post(ANILIST_GRAPHQL_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        return response.json()["data"]["User"]["id"]
    except requests.HTTPError as e:
        #TODO Correct error response
        print('ERROR WRONG RESPONSE CODE')
    except Exception as e:
        #TODO Correct error response
        print('UNKNOWN Error when trying to get user id :')
        print(e)
    return None


def get_latest_users_activities(users_id, page, perPage = 5):
    """ Get latest users' activities """

    query = '''query ($userIds: [Int], $page: Int, $perPage: Int) {
        Page (page: $page, perPage: $perPage) {
            activities (userId_in: $userIds, sort: ID_DESC) {
                __typename
                ... on ListActivity {
                    id
                    type
                    status
                    progress
                    isLocked
                    createdAt
                    
                    user {
                        id
                        name
                    }

                    media {
                        id
                        siteUrl
                        episodes
                        chapters
                        title {
                            romaji
                            english
                            native
                        }
                        coverImage {
                            large
                        }
                    }
                } 
            } 
        }
    }'''

    variables = {
        "userIds": DEBUG_USERS,
        "perPage": perPage,
        "page": page
    }

    try:
        response = requests.post(ANILIST_GRAPHQL_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        return response.json()["data"]["Page"]["activities"]
    except requests.HTTPError as e:
        #TODO Correct error response
        print('ERROR WRONG RESPONSE CODE')
    except Exception as e:
        #TODO Correct error response
        print('UNKNOWN Error when trying to get the users\' activities :')
        print(e)
    return None


def get_latest_activity(users_id):
    """ Get the latest users' activity """

    # TODO Will fail if last activity is not a ListActivity
    query = '''query ($userIds: [Int]) {
        Activity(userId_in: $userIds, sort: ID_DESC) {
            __typename
            ... on ListActivity {
                id
                userId
                createdAt
            } 
        }
    }'''

    variables = {
        "userIds": users_id
    }

    try:
        response = requests.post(ANILIST_GRAPHQL_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        return response.json()["data"]["Activity"]
    except requests.HTTPError as e:
        #TODO Correct error response
        print('ERROR WRONG RESPONSE CODE')
    except Exception as e:
        #TODO Correct error response
        print('UNKNOWN Error when trying to get the latest activity :')
        print(e)
    return None


def get_media_name(activity):
    ''' Returns the media name in english if possible '''

    english_name = activity["media"]["title"]["english"]
    if english_name is not None:
        return english_name

    romaji_name = activity["media"]["title"]["romaji"]
    if romaji_name is not None:
        return romaji_name

    native_name = activity["media"]["title"]["native"]
    if native_name is not None:
        return native_name

    return ''


def get_progress(activity):
    progress = activity["progress"]
    if progress is None:
        return '?'
    return progress


def build_status_string(activity):
    status_str = activity["status"].capitalize()
    status = MediaListStatus.from_str(status_str)
    progress = get_progress(activity)
    episodes = ''
    media_label = ''
    media_type = MediaType.from_str(activity["type"])

    # TODO Manage Completed/Dropped/Planned episodes/chapters count
    if media_type.ANIME:
        episodes = activity["media"]["episodes"]
        if episodes is None:
            episodes = '?'
        media_label = 'episodes'
    elif media_type.MANGA:
        episodes = activity["media"]["chapters"]
        if episodes is None:
            episodes = '?'
        media_label = 'chapters'

    return '{} - {} of {} {}'.format(status_str, progress, episodes, media_label)


async def send_embed_to_channels(activity):

    image = activity["media"]["coverImage"]["large"]
    user_name = activity["user"]["name"]
    media_name = get_media_name(activity)
    media_url = activity["media"]["siteUrl"]
    published_date = datetime.datetime.fromtimestamp(activity["createdAt"])
    status_str = build_status_string(activity)

    user_data = utils.get_user_data()
    servers = user_data["servers"].split(",")
    for server in servers:
        data_channels = utils.get_channels(server)
    
        if data_channels is not None:
            for channel in data_channels:
                await myanimebot.send_embed_wrapper(None,
                                                    channel["channel"],
                                                    globals.client,
                                                    myanimebot.build_embed(user_name, media_name, media_url, status_str, published_date, image, utils.Service.ANILIST))


def insert_feed_db(activity):
    user_name = activity["user"]["name"]
    media_name = get_media_name(activity)
    media_url = activity["media"]["siteUrl"]
    published_date = datetime.datetime.fromtimestamp(activity["createdAt"]).isoformat()
    status = activity["status"]

    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type, service) VALUES (%s, %s, %s, %s, NOW(), %s, %s)",
                    (published_date,
                     media_name,
                     media_url,
                     user_name,
                     status, # TODO Create enum to make it generic
                     globals.SERVICE_ANILIST))
    globals.conn.commit()


async def process_new_activities(last_activity_date):
    """ Fetch and process all newest activities """
    
    continue_fetching = True
    page_number = 1
    while continue_fetching:
        # Get activities
        activities = get_latest_users_activities(DEBUG_USERS, page_number)

        # Processing them
        for activity in activities:
            # Check if activity is a ListActivity
            if activity["__typename"] != 'ListActivity':
                continue

            print(activity) # TODO Remove, DEBUG

            # Get time difference between now and activity creation date
            diffTime = datetime.datetime.now(globals.timezone) - datetime.datetime.fromtimestamp(activity["createdAt"], globals.timezone)

            print("Time difference between feed and now = {}".format(diffTime))
            # If the activity is older than the last_activity_date, we processed all the newest activities
            # Also, if the time difference is bigger than the config's "secondMax", we can stop processing them
            if activity["createdAt"] <= last_activity_date or diffTime.total_seconds() > globals.secondMax:
                # FIXME If two or more feeds are published at the same time, this would skip them
                continue_fetching = False
                break
            # Process activity
            # TODO Add logger infos
            insert_feed_db(activity)
            # TODO Create embed and send to channels
            await send_embed_to_channels(activity)

        # Load next activities page
        # TODO How can I avoid duplicate if insertion in between? With storing ids?
        if continue_fetching:
            print('Fetching next page') # TODO Remove, Debug
            page_number += 1
            time.sleep(1)


def get_last_activity_date_db():
    # Refresh database
    globals.conn.commit()

    # Get last activity date
    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("SELECT published FROM t_feeds WHERE service=%s ORDER BY published DESC LIMIT 1", [globals.SERVICE_ANILIST])
    data = cursor.fetchone()

    print("Getting last activity date : {}".format(data))
    if data is None or len(data) == 0:
        return 0
    else:
        return data[0].timestamp()


async def check_new_activities():
    """ Check if there is new activities and process them """
    
    # last_activity_date = 1608340203 # TODO SELECT DATE IN DB
    last_activity_date = get_last_activity_date_db()
    print(last_activity_date)

    # Get latest activity on AniList
    latest_activity = get_latest_activity(DEBUG_USERS)
    if latest_activity is not None:

        # If the latest activity is more recent than the last we stored
        if last_activity_date < latest_activity["createdAt"]:
            print("Latest activity is more recent")
            await process_new_activities(last_activity_date)
            

# [x] Convertir AniList ID en MAL ID
# [ ] Recuperer utilisateurs qui nous interessent
# [X] Recuperer activites de ces users
# [X] Traiter les donnees et les mettre en DB
# [X] Creer embed et envoyer messages
# [ ] Faire task pour fetch automatiquement
# [ ] Rajouter requests dans la liste de dependances pip (Site de Penta)

# TODO Changer titre (Pour l'instant c'est MAL de XXX)
# TODO Bien renvoyer vers AniList (Liens/Liste/Anime)
# TODO Recuperer image d'AniList
# TODO Comment eviter doublons MAL/AniList
