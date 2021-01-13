import re
import urllib
import datetime

from bs4 import BeautifulSoup

import myanimebot.utils as utils
import myanimebot.globals as globals

def get_thumbnail(urlParam):
    ''' Returns the MAL media thumbnail from a link '''

    url = "/".join((urlParam).split("/")[:5])
	
    websource = urllib.request.urlopen(url)
    soup = BeautifulSoup(websource.read(), "html.parser")
    image = re.search(r'(?P<url>https?://[^\s]+)', str(soup.find("img", {"itemprop": "image"}))).group("url")
    thumbnail = "".join(image.split('"')[:1]).replace('"','')
	
    return thumbnail


def build_feed_from_data(data, user : utils.User, image, pubDateRaw, type : utils.MediaType) -> utils.Feed:
    if data is None: return None

    if data.description.startswith('-') :
        if type == utils.MediaType.MANGA:
            data.description = "Re-reading " + data.description
        else:
            data.description = "Re-watching " + data.description								

    status, progress, episodes = break_rss_description_string(data.description)

    media = utils.Media(name=data.title,
                        url=data.link,
                        episodes=episodes,
                        image=image,
                        type=type)

    feed = utils.Feed(service=utils.Service.MAL,
                        date_publication=datetime.datetime.fromtimestamp(pubDateRaw, globals.timezone),
                        user=user,
                        status=status,
                        description=data.description, # TODO To remove, useless now
                        media=media,
                        progress=progress)
    return feed


def break_rss_description_string(description : str):
    ''' Break a MyAnimeList RSS description from a feed into a Status, the progress and the number of episodes '''

    # Description example: "Completed - 12 of 12 episodes"

    # Split the description starting from the dash
    split_desc = description.rsplit('-', 1)
    if (len(split_desc) != 2):
        globals.logger.error("Error while trying to break MAL RSS description. No '-' found in '{}'.".format(description))
        return None, None, None

    status_str = split_desc[0]
    episodes_progress_and_count = split_desc[1]
    status = utils.MediaStatus.from_str(status_str)

    # Split the second part of the string (E.g. "12 of 12 episodes") to get the progress
    episodes_progress_and_count_split = episodes_progress_and_count.split('of', 1)
    if (len(episodes_progress_and_count_split) != 2):
        globals.logger.error("Error while trying to break MAL RSS description. No 'of' found between the progress and the episode count in '{}'.".format(description))
        return None, None, None

    progress = episodes_progress_and_count_split[0].strip()
    episodes_count_str = episodes_progress_and_count_split[1].strip()

    # Remove the episodes label from our string
    episode_count_split = episodes_count_str.split(' ', 1)
    if (len(episode_count_split) != 2):
        globals.logger.error("Error while trying to break MAL RSS description. No space found between the episode count and the label episodes in '{}'.".format(description))
        return None, None, None

    episodes_count = episode_count_split[0]

    return status, progress, episodes_count