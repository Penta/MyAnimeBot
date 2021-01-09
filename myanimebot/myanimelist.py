import re
import urllib
import datetime

from bs4 import BeautifulSoup

import myanimebot.utils as utils
import myanimebot.globals as globals

def get_thumbnail(urlParam):
    ''' Returns the MAL media thumnail from a link '''

    url = "/".join((urlParam).split("/")[:5])
	
    websource = urllib.request.urlopen(url)
    soup = BeautifulSoup(websource.read(), "html.parser")
    image = re.search(r'(?P<url>https?://[^\s]+)', str(soup.find("img", {"itemprop": "image"}))).group("url")
    thumbnail = "".join(image.split('"')[:1]).replace('"','')
	
    print(thumbnail)
    return thumbnail


def build_feed_from_data(data, user : utils.User, image, pubDateRaw, type : utils.MediaType) -> utils.Feed:
    if data is None: return None

    media = utils.Media(name=data.title,
                        url=data.link,
                        episodes=None,
                        image=image,
                        type=type)
    feed = utils.Feed(service=utils.Service.MAL,
                        date_publication=datetime.datetime.fromtimestamp(pubDateRaw, globals.timezone),
                        user=user,
                        status=data.description,
                        description=data.description,
                        media=media)
    return feed
