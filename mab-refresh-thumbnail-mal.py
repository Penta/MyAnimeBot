#!/usr/bin/env python3
# Copyright Penta (c) 2018/2020 - Under BSD License

# Compatible for Python 3.6.X
#
# Check and update all the thumbnail for manga/anime in the MyAnimeBot database.
# Can be pretty long and send a lot of request to MyAnimeList.net,
# Use it only once in a while to clean the database.
#
# Dependencies (for CentOS 7):
# yum install python3 mariadb-devel gcc python3-devel
# python3.6 -m pip install --upgrade pip
# pip3.6 install mysql python-dateutil asyncio html2text bs4 aiodns cchardet configparser
# pip3.6 install mysql.connector

# Library import
import os
import re
import asyncio
import urllib.request
import string
import time
import socket

from html2text import HTML2Text
from bs4 import BeautifulSoup
from configparser import ConfigParser

# Custom library
from myanimebot.myanimelist import get_thumbnail
import myanimebot.globals as globals

# Script version
VERSION = "1.2"

globals.logger.info("Booting the MyAnimeBot Thumbnail Refresher " + VERSION + "...")

def main() :
	globals.logger.info("Starting the refresher task...")
	
	count = 0
	
	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("SELECT guid, title, thumbnail FROM t_animes")
	datas = cursor.fetchall()
	
	globals.logger.info(str(len(datas)) + " medias are going to be checked.")

	for data in datas:
		try:
			image = get_thumbnail(data[0])
			
			if (image == data[2]) :
				if (image != "") :
					globals.logger.debug("Thumbnail for " + str(data[1]) + " already up to date.")
				else :
					globals.logger.info("Thumbnail for " + str(data[1]) + " still empty.")
			else :
				if (image != "") :
					cursor.execute("UPDATE t_animes SET thumbnail = %s WHERE guid = %s", [image, data[0]])
					globals.conn.commit()
					
					globals.logger.info("Updated thumbnail found for \"" + str(data[1]) + "\": %s", image)
					count += 1
				else :
					try :
						urllib.request.urlopen(data[2])
						globals.logger.info("Thumbnail for \"" + str(data[1]) + "\" is now empty, avoiding change.")
					except :
						globals.logger.info("Thumbnail for \"" + str(data[1]) + "\" has been deleted!")
		except Exception as e :
			globals.logger.warning("Error while updating thumbnail for '" + str(data[1]) + "': " + str(e))

		time.sleep(3)
	
	globals.logger.info("All thumbnails checked!")
	cursor.close()
	
	globals.logger.info(str(count) + " new thumbnails, time taken: %ss" % round((time.time() - startTime), 2))

# Starting main function
if __name__ == "__main__" :
	startTime = time.time()
	main()

	globals.logger.info("Thumbnail refresher script stopped")
	
	# We close all the ressources
	globals.conn.close()
