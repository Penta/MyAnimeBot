import asyncio
import datetime
import time
from enum import Enum
from typing import Dict, List

import requests

import myanimebot.globals as globals
import myanimebot.utils as utils

ANILIST_GRAPHQL_URL = 'https://graphql.anilist.co'

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
    media_type = utils.MediaType.from_str(activity["type"])

    # TODO Manage Completed/Dropped/Planned episodes/chapters count
    if status == MediaListStatus.CURRENT \
       or status == MediaListStatus.REPEATING:
        if media_type == utils.MediaType.ANIME:
            episodes = activity["media"]["episodes"]
            if episodes is None:
                episodes = '?'
            media_label = 'episodes'
        elif media_type == utils.MediaType.MANGA:
            episodes = activity["media"]["chapters"]
            if episodes is None:
                episodes = '?'
            media_label = 'chapters'
        return '{} | {} of {} {}'.format(status_str, progress, episodes, media_label)

    else:
        return '{}'.format(status_str)


def build_feed_from_activity(activity, user : utils.User):
    if activity is None: return None

    media = utils.Media(name=get_media_name(activity),
                        url=activity["media"]["siteUrl"],
                        episodes=utils.Media.get_number_episodes(activity),
                        image=activity["media"]["coverImage"]["large"],
                        type=utils.MediaType.from_str(activity["media"]["type"]))
    feed = utils.Feed(service=utils.Service.ANILIST,
                        date_publication=datetime.datetime.fromtimestamp(activity["createdAt"], globals.timezone),
                        user=user,
                        status=build_status_string(activity),
                        description=activity["status"],
                        media=media)
    return feed
 

def get_anilist_userId_from_name(user_name : str) -> int:
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


def get_latest_users_activities(users : List[utils.User], page: int, perPage = 5) -> List[utils.Feed]:
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
                        type
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
        "userIds": [user.service_id for user in users],
        "perPage": perPage,
        "page": page
    }

    try:
        # Execute GraphQL query
        response = requests.post(ANILIST_GRAPHQL_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        data = response.json()["data"]["Page"]["activities"]

        # Create feeds from data
        feeds = []
        for activity in data:
            # Check if activity is a ListActivity
            if activity["__typename"] != 'ListActivity':
                continue
            
            # Find corresponding user for this ListActivity
            user = next((user for user in users if user.name == activity["user"]["name"]), None)
            if user is None:
                raise RuntimeError('Cannot find {} in our registered users'.format(activity["user"]["name"]))

            # Add new builded feed
            feeds.append(build_feed_from_activity(activity, user))
        return feeds

    except requests.HTTPError as e:
        #TODO Correct error response
        print('ERROR WRONG RESPONSE CODE')
    except Exception as e:
        #TODO Correct error response
        print('UNKNOWN Error when trying to get the users\' activities :')
        print(e)
    return []


def check_username_validity(username) -> bool:
    """ Check if the AniList username exists """

    query = '''query($name: String) {
        User(name: $name) {
            name
        }
    }'''

    variables = {
        'name': username
    }

    try:
        response = requests.post(ANILIST_GRAPHQL_URL, json={'query': query, 'variables': variables})
        response.raise_for_status()
        return response.json()["data"]["User"]["name"] == username
    except requests.HTTPError as e:
        return False
    except Exception as e:
        #TODO Correct error response
        print('UNKNOWN Error when trying to get mal id : {}'.format(e))
        return False


def get_latest_activity(users : List[utils.User]):
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
        "userIds": [user.service_id for user in users]
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


def get_users_db():
    ''' Returns the registered users using AniList '''

	# TODO Make generic execute
    cursor = globals.conn.cursor(buffered=True, dictionary=True)
    cursor.execute("SELECT id, {}, servers FROM t_users WHERE service = %s".format(globals.DB_USER_NAME), [globals.SERVICE_ANILIST])
    users_data = cursor.fetchall()
    cursor.close()
    return users_data


def get_users() -> List[utils.User]:
    users = []
    users_data = get_users_db()
    if users_data is not None:
        for user_data in users_data:
            users.append(utils.User(id=user_data["id"],
                            service_id=get_anilist_userId_from_name(user_data[globals.DB_USER_NAME]),
                            name=user_data[globals.DB_USER_NAME],
                            servers=user_data["servers"].split(',')))
    return users


def get_users_id(users_data) -> List[int]:
    ''' Returns the id of the registered users using AniList '''

    users_ids = []

    # Get users using AniList
    if users_data is not None:
        print("Users found: {}".format(users_data))
        for user_data in users_data:
            users_ids.append(get_anilist_userId_from_name(user_data[globals.DB_USER_NAME]))
        # TODO Normalement pas besoin de recuperer les ids vu que je peux faire la recherche avec les noms

    return users_ids


async def send_embed_to_channels(activity : utils.Feed):
    # TODO Doc
    for server in activity.user.servers:
        data_channels = utils.get_channels(server)
    
        if data_channels is not None:
            for channel in data_channels:
                await utils.send_embed_wrapper(None,
                                                    channel["channel"],
                                                    globals.client,
                                                    utils.build_embed(activity.user.name,
                                                                            activity.media.name,
                                                                            activity.media.url,
                                                                            activity.status,
                                                                            activity.date_publication,
                                                                            activity.media.image,
                                                                            activity.service))


def insert_feed_db(activity: utils.Feed):
    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type, service) VALUES (FROM_UNIXTIME(%s), %s, %s, %s, NOW(), %s, %s)",
                    (activity.date_publication.timestamp(),
                     activity.media.name,
                     activity.media.url,
                     activity.user.name,
                     activity.description, # TODO Create enum to make it generic
                     globals.SERVICE_ANILIST))
    globals.conn.commit()


async def process_new_activities(last_activity_date, users : List[utils.User]):
    """ Fetch and process all newest activities """
    
    continue_fetching = True
    page_number = 1
    while continue_fetching:
        # Get activities
        activities = get_latest_users_activities(users, page_number)

        # Processing them
        for activity in activities:
            print(activity) # TODO Remove, DEBUG

            # Get time difference between now and activity creation date
            diffTime = datetime.datetime.now(globals.timezone) - activity.date_publication
            print("Time difference between feed and now = {}".format(diffTime))

            # If the activity is older than the last_activity_date, we processed all the newest activities
            # Also, if the time difference is bigger than the config's "secondMax", we can stop processing them
            if activity.date_publication.timestamp() <= last_activity_date \
                 or diffTime.total_seconds() > globals.secondMax:
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


def get_last_activity_date_db() -> float:
    # Refresh database
    globals.conn.commit()

    # Get last activity date
    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("SELECT published FROM t_feeds WHERE service=%s ORDER BY published DESC LIMIT 1", [globals.SERVICE_ANILIST])
    data = cursor.fetchone()

    if data is None or len(data) == 0:
        return 0.0
    else:
        return data[0].timestamp()


async def check_new_activities():
    """ Check if there is new activities and process them """
    
    last_activity_date = get_last_activity_date_db()

    # Get latest activity on AniList
    users = get_users()
    latest_activity = get_latest_activity(users)
    if latest_activity is not None:

        # If the latest activity is more recent than the last we stored
        print('Last registered = {} | {} = latest feed'.format(last_activity_date, latest_activity["createdAt"]))
        if last_activity_date < latest_activity["createdAt"]:
            globals.logger.debug("Found a more recent AniList feed")
            await process_new_activities(last_activity_date, users)


async def background_check_feed(asyncioloop):
    ''' Main function that check the AniList feeds '''

    globals.logger.info("Starting up Anilist.background_check_feed")
    await globals.client.wait_until_ready()	
    globals.logger.debug("Discord client connected, unlocking Anilist.background_check_feed...")

    while not globals.client.is_closed():
        globals.logger.debug('Fetching Anilist feeds')
        try:
            await check_new_activities()
        except Exception as e:
            globals.logger.error('Error while fetching Anilist feeds : ({})'.format(e))

        await asyncio.sleep(globals.ANILIST_SECONDS_BETWEEN_FETCHES)


# TODO Bien renvoyer vers AniList (Liens/Liste/Anime)
# TODO Comment eviter doublons MAL/AniList -> Ne pas faire je pense
# TODO Insert anime into DB
# TODO Uniformiser labels status feed entre MAL et ANILIST