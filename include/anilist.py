import requests
from enum import Enum

ANILIST_GRAPHQL_URL='https://graphql.anilist.co'

class MediaType(Enum):
    ANIME="ANIME"
    MANGA="MANGA"

def anilist_id_to_mal(media_id, media_type: MediaType):
    """ Convert an AniList media ID to a MyAnimeList ID and returns it """

    query = '''query($id: Int, $type: MediaType){
        Media(id: $id, type: $type) {
            idMal
        }
    }'''

    variables = {
        'id': media_id,
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


print(anilist_id_to_mal(110277, MediaType.ANIME))


# [x] Convertir AniList ID en MAL ID
# [ ] Recuperer utilisateurs qui nous interessent
# [ ] Recuperer activites de ces users
# [ ] Traiter les donnees et les mettre en DB
# [ ] Faire task pour fetch automatiquement
# [ ] Rajouter requests dans la liste de dependances pip (Site de Penta)