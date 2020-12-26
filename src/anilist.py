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
                        title {
                            romaji
                            english
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


async def send_embed_to_channels(activity):

    # Fetch user's data
    try:
        db_user = globals.conn.cursor(buffered=True)
        db_user.execute("SELECT mal_user, servers FROM t_users")
        data_user = db_user.fetchone()
    except Exception as e:
        # TODO Catch exception
        globals.logger.critical("Database unavailable! (" + str(e) + ")")
        quit()

    # TODO Fetch and insert AniList thumbnail
    # Fetch image's data
    # cursor.execute("SELECT thumbnail FROM t_animes WHERE guid=%s LIMIT 1", [item.guid])
    # data_img = cursor.fetchone()
    
    # if data_img is None:
    try:
        # TODO Directly send malId instead
        image = get_thumbnail_from_anilist_id(activity["media"]["id"], MediaType.from_str(activity["type"]))
        
        globals.logger.info("First time seeing this " + activity["media"]["title"]["english"] + ", adding thumbnail into database: " + image)
    except Exception as e:
        globals.logger.warning("Error while getting the thumbnail: " + str(e))
        image = ""
            
        # cursor.execute("INSERT INTO t_animes (guid, title, thumbnail, found, discoverer, media) VALUES (%s, %s, %s, NOW(), %s, %s)", [item.guid, item.title, image, user, media])
        # globals.conn.commit()
    # else: image = data_img[0]


    for server in data_user[1].split(","):
        db_srv = globals.conn.cursor(buffered=True)
        db_srv.execute("SELECT channel FROM t_servers WHERE server = %s", [server])
        data_channel = db_srv.fetchone()
    
        # FIXME 'Completed None'
        while data_channel is not None:
            for channel in data_channel:
                await myanimebot.send_embed_wrapper(None,
                                                    channel,
                                                    globals.client,
                                                    myanimebot.build_embed(activity["user"]["name"],
                                                                            activity["media"]["title"]["english"],
                                                                            activity["media"]["siteUrl"],
                                                                            "{} {}".format(activity["status"], activity["progress"]),
                                                                            datetime.datetime.fromtimestamp(activity["createdAt"]),
                                                                            image))
            
            data_channel = db_srv.fetchone()



def insert_feed_db(activity):
    cursor = globals.conn.cursor(buffered=True)

    cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type, service) VALUES (%s, %s, %s, %s, NOW(), %s, %s)",
                    (datetime.datetime.fromtimestamp(activity["createdAt"]).isoformat(),
                     activity["media"]["title"]["english"], # TODO When getting title if no english take romaji
                     activity["media"]["siteUrl"], # TODO Get siteurl from MAL I guess
                     activity["user"]["name"], # TODO Same user than mal one
                     activity["status"], # TODO Create enum to make it generic
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
