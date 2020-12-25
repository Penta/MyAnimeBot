import requests
import time
import datetime
from enum import Enum

import globals

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


def process_new_activities(last_activity_date):
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
            # If the activity is older than the last_activity_date, we processed all the newest activities
            # Also, if the time difference is bigger than the config's "secondMax", we can stop processing them
            if activity["createdAt"] < last_activity_date or diffTime.total_seconds() > globals.secondMax:
                continue_fetching = False
                break
            # Process activity
            # TODO Add logger infos
            insert_feed_db(activity)
            # TODO Create embed and send to channels

        # Load next activities page
        # TODO How can I avoid duplicate if insertion in between? With storing ids?
        if continue_fetching:
            print('Fetching next page') # TODO Remove, Debug
            page_number += 1
            time.sleep(1)


def get_last_activity_date_db():
    cursor = globals.conn.cursor(buffered=True)
    cursor.execute("SELECT published FROM t_feeds WHERE service=%s ORDER BY published DESC LIMIT 1", [globals.SERVICE_ANILIST])
    data = cursor.fetchone()

    print(data)
    if data is None:
        return 0
    else:
        return int(data)


def check_new_activities():
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
            process_new_activities(last_activity_date)
            

# [x] Convertir AniList ID en MAL ID
# [ ] Recuperer utilisateurs qui nous interessent
# [X] Recuperer activites de ces users
# [X] Traiter les donnees et les mettre en DB
# [ ] Creer embed et envoyer messages
# [ ] Faire task pour fetch automatiquement
# [ ] Rajouter requests dans la liste de dependances pip (Site de Penta)