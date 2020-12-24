import requests
import time
from enum import Enum

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
                    userId
                    type
                    status
                    progress
                    isLocked
                    createdAt
                    media {
                        id
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


def process_new_activities(last_activity_date):
    """ Fetch and process all newest activities """
    
    continue_fetching = True
    page_number = 1
    while continue_fetching:
        # Get activities
        activities = get_latest_users_activities(DEBUG_USERS, page_number)

        # Processing them
        for activity in activities:
            print(activity) # TODO Remove, DEBUG
            # If the activity is older than the last_activity_date, we processed all the newest activities
            if activity["createdAt"] < last_activity_date:
                continue_fetching = False
                break
            # Process activity
            # TODO Insert in DB

        # Load next activities page
        # TODO How can I avoid duplicate if insertion in between? With storing ids?
        if continue_fetching:
            print('Fetching next page') # TODO Remove, Debug
            page_number += 1
            time.sleep(1)


def check_new_activities():
    """ Check if there is new activities and process them """
    
    last_activity_date = 1608340203 # TODO SELECT DATE IN DB

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
# [ ] Traiter les donnees et les mettre en DB
# [ ] Faire task pour fetch automatiquement
# [ ] Rajouter requests dans la liste de dependances pip (Site de Penta)