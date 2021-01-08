import re
import urllib

from bs4 import BeautifulSoup


def get_thumbnail(urlParam):
    ''' Returns the MAL media thumnail from a link '''

    url = "/".join((urlParam).split("/")[:5])
	
    websource = urllib.request.urlopen(url)
    soup = BeautifulSoup(websource.read(), "html.parser")
    image = re.search(r'(?P<url>https?://[^\s]+)', str(soup.find("img", {"itemprop": "image"}))).group("url")
    thumbnail = "".join(image.split('"')[:1]).replace('"','')
	
    print(thumbnail)
    return thumbnail
