#!/usr/bin/env python3
# Copyright Penta (c) 2018/2021 - Under BSD License

# Library import
import os
import re
import asyncio
import urllib.request
import string
import time
import socket

# Custom library
from myanimebot.myanimelist import get_thumbnail
import myanimebot.globals as globals

# Script version
VERSION = "1.2"

globals.logger.info("Booting the MyAnimeBot Thumbnail Refresher " + VERSION + "...")

def refresh_thumbnail_mal(startTime) :
	globals.logger.info("Starting the refresher task...")
	
	count = 0
	
	cursor = globals.conn.cursor(buffered=True)
	cursor.execute("SELECT guid, title, thumbnail FROM t_animes WHERE service = %s", [globals.SERVICE_MAL])
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
					except Exception as e :
						globals.logger.info("Thumbnail for \"" + str(data[1]) + "\" has been deleted! (" + str(e) + ")")
		except Exception as e :
			globals.logger.warning("Error while updating thumbnail for '" + str(data[1]) + "': " + str(e))

		time.sleep(globals.MYANIMELIST_SECONDS_BETWEEN_REQUESTS)
	
	globals.logger.info("All thumbnails checked!")
	cursor.close()
	
	globals.logger.info(str(count) + " new thumbnails, time taken: %ss" % round((time.time() - startTime), 2))

# Starting main function
if __name__ == "__main__" :
	refresh_thumbnail_mal(time.time())

	globals.logger.info("Thumbnail refresher script stopped")
	
	# We close all the ressources
	globals.conn.close()
