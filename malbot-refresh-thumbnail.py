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
import logging
import os
import re
import asyncio
import urllib.request
import mysql.connector as mariadb
import string
import time
import socket

from html2text import HTML2Text
from bs4 import BeautifulSoup
from configparser import ConfigParser

# Custom library
import utils

class ImproperlyConfigured(Exception): pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser("~")

DEFAULT_CONFIG_PATHS = [
	os.path.join("myanimebot.conf"),
	os.path.join(BASE_DIR, "myanimebot.conf"),
	os.path.join("/etc/malbot/myanimebot.conf"),
	os.path.join(HOME_DIR, "myanimebot.conf")
]

def get_config():
	config = ConfigParser()
	config_paths = []

	for path in DEFAULT_CONFIG_PATHS:
		if os.path.isfile(path):
			config_paths.append(path)
			break
	else: raise ImproperlyConfigured("No configuration file found")
		
	config.read(config_paths)

	return config

# Loading configuration
try:
	config=get_config()
except Exception as e:
	print ("Cannot read configuration: " + str(e))
	exit (1)
	
CONFIG=config["MYANIMEBOT"]
logLevel=CONFIG.get("logLevel", "INFO")
dbHost=CONFIG.get("dbHost", "127.0.0.1")
dbUser=CONFIG.get("dbUser", "myanimebot")
dbPassword=CONFIG.get("dbPassword")
dbName=CONFIG.get("dbName", "myanimebot")
logPath=CONFIG.get("logPath", "myanimebot.log")

# class that send logs to DB
class LogDBHandler(logging.Handler):
	'''
	Customized logging handler that puts logs to the database.
	pymssql required
	'''
	def __init__(self, sql_conn, sql_cursor):
		logging.Handler.__init__(self)
		self.sql_cursor = sql_cursor
		self.sql_conn   = sql_conn

	def emit(self, record):	
		# Clear the log message so it can be put to db via sql (escape quotes)
		self.log_msg = str(record.msg.strip().replace('\'', '\'\''))
		
		# Make the SQL insert
		try:
			self.sql_cursor.execute("INSERT INTO t_logs (host, level, type, log, date, source) VALUES (%s, %s, %s, %s, NOW(), %s)", (str(socket.gethostname()), str(record.levelno), str(record.levelname), self.log_msg, str(record.name)))
			self.sql_conn.commit()
		except Exception as e:
			print ('Error while logging into DB: ' + str(e))


# Log configuration
log_format='%(asctime)-13s : %(name)-15s : %(levelname)-8s : %(message)s'
logging.basicConfig(handlers=[logging.FileHandler(logPath, 'a', 'utf-8')], format=log_format, level=logLevel)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(log_format))

logger = logging.getLogger("thumbnailer")
logger.setLevel(logLevel)

logging.getLogger('').addHandler(console)

# Script version
VERSION = "1.1"

logger.info("Booting the MyAnimeBot Thumbnail Refresher " + VERSION + "...")

# Initialization of the database
try:
	conn = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName, buffered=True)
	
	# We initialize the logs into the DB.
	log_conn   = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName, buffered=True)
	log_cursor = log_conn.cursor()
	logdb = LogDBHandler(log_conn, log_cursor)
	logging.getLogger('').addHandler(logdb)
except Exception as e :
	logger.critical("Can't connect to the database: " + str(e))
	
	httpclient.close()
	quit()

def main() :
	logger.info("Starting the refresher task...")
	
	count = 0
	
	cursor = conn.cursor(buffered=True)
	cursor.execute("SELECT guid, title, thumbnail FROM t_animes")
	datas = cursor.fetchall()
	
	logger.info(str(len(datas)) + " medias are going to be checked.")

	for data in datas:
		try:
			image = utils.getThumbnail(data[0])
			
			if (image == data[2]) :
				if (image != "") :
					logger.debug("Thumbnail for " + str(data[1]) + " already up to date.")
				else :
					logger.info("Thumbnail for " + str(data[1]) + " still empty.")
			else :
				if (image != "") :
					cursor.execute("UPDATE t_animes SET thumbnail = %s WHERE guid = %s", [image, data[0]])
					conn.commit()
					
					logger.info("Updated thumbnail found for \"" + str(data[1]) + "\": %s", image)
					count += 1
				else :
					try :
						urllib.request.urlopen(data[2])
						logger.info("Thumbnail for \"" + str(data[1]) + "\" is now empty, avoiding change.")
					except :
						logger.info("Thumbnail for \"" + str(data[1]) + "\" has been deleted!")
		except Exception as e :
			logger.warning("Error while updating thumbnail for '" + str(data[1]) + "': " + str(e))

		time.sleep(3)
	
	logger.info("All thumbnails checked!")
	cursor.close()
	
	logger.info(str(count) + " new thumbnails, time taken: %ss" % round((time.time() - startTime), 2))

# Starting main function
if __name__ == "__main__" :
	startTime = time.time()
	main()

	logger.info("Thumbnail refresher script stopped")
	
	# We close all the ressources
	conn.close()
