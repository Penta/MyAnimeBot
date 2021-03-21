import logging
import os
import socket
from configparser import ConfigParser

import discord
import pytz
import feedparser
import mariadb
import psycopg2
import pytz


class ImproperlyConfigured(Exception): pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser("~")

DEFAULT_CONFIG_PATHS = [
	os.path.join("myanimebot.conf"),
	os.path.join(BASE_DIR, "myanimebot.conf"),
	os.path.join("/etc/myanimebot/myanimebot.conf"),
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
dbType=CONFIG.get("database.type", "mariadb")
dbMariaHost=CONFIG.get("mariadb.host", "127.0.0.1")
dbMariaPort=CONFIG.get("mariadb.port", "3306")
dbMariaUser=CONFIG.get("mariadb.user", "myanimebot")
dbMariaPassword=CONFIG.get("mariadb.password")
dbMariaName=CONFIG.get("mariadb.name", "myanimebot")
dbMariaSSLenabled=CONFIG.getboolean("mariadb.ssl", False)
dbMariaSSLca=CONFIG.get("mariadb.ssl.ca")
dbMariaSSLcert=CONFIG.get("mariadb.ssl.cert")
dbMariaSSLkey=CONFIG.get("mariadb.ssl.key")
dbPgHost=CONFIG.get("postgresql.host", "127.0.0.1")
dbPgPort=CONFIG.get("postgresql.port", "5432")
dbPgUser=CONFIG.get("postgresql.user", "myanimebot")
dbPgPassword=CONFIG.get("postgresql.password")
dbPgName=CONFIG.get("postgresql.name", "myanimebot")
logPath=CONFIG.get("logPath", "myanimebot.log")
timezone=pytz.timezone(CONFIG.get("timezone", "utc"))
secondMax=CONFIG.getint("secondMax", 7200)
token=CONFIG.get("token")
prefix=CONFIG.get("prefix", "!mab")
MYANIMELIST_SECONDS_BETWEEN_REQUESTS=CONFIG.getint("myanimelist_seconds_between_requests", 2)
iconBot=CONFIG.get("iconBot", "http://myanimebot.pentou.eu/rsc/bot_avatar.jpg")
ANILIST_SECONDS_BETWEEN_FETCHES=CONFIG.getint("anilist_seconds_between_fetches", 60)
MAL_ICON_URL=CONFIG.get("iconMAL", "https://cdn.myanimelist.net/img/sp/icon/apple-touch-icon-256.png")
ANILIST_ICON_URL=CONFIG.get("iconAniList", "https://anilist.co/img/icons/android-chrome-512x512.png")
SERVICE_ANILIST="ani"
SERVICE_MAL="mal"
MAL_URL="https://myanimelist.net/"
MAL_PROFILE_URL="https://myanimelist.net/profile/"
ANILIST_PROFILE_URL="https://anilist.co/user/"
DB_USER_NAME="mal_user" # Column's name for usernames in the t_users table
MAL_ENABLED=CONFIG.getboolean("mal_enabled", True)
ANI_ENABLED=CONFIG.getboolean("ani_enabled", True)
HEALTHCHECK_ENABLED=CONFIG.getboolean("healthcheck_enabled", False)
HEALTHCHECK_PORT=CONFIG.getint("healthcheck_port", 15200)
HEALTHCHECK_IP=CONFIG.get("healthcheck_ip", "0.0.0.0")

# Log configuration
log_format='%(asctime)-13s : %(name)-15s : %(levelname)-8s : %(message)s'
logging.basicConfig(handlers=[logging.FileHandler(logPath, 'a', 'utf-8')], format=log_format, level=logLevel)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(log_format))

logger = logging.getLogger("myanimebot")
logger.setLevel(logLevel)

logging.getLogger('').addHandler(console)

# Script version
VERSION = "1.0.0a"

logger.info("Booting MyAnimeBot " + VERSION + "...")
logger.debug("DEBUG log: OK")

# feedparser.PREFERRED_XML_PARSERS.remove("drv_libxml2")

# Initialization of the database
try:
	# Main database connection
	if (dbType.lower() == "mariadb") or (dbType.lower() == "mysql") :
		if (dbSSLenabled) :
			conn = mariadb.connect(host=dbMariaHost, user=dbMariaUser, password=dbMariaPassword, database=dbMariaName, port=dbMariaPort, ssl_ca=dbMariaSSLca, ssl_cert=dbMariaSSLcert, ssl_key=dbMariaSSLkey)
		else :
			conn = mariadb.connect(host=dbMariaHost, user=dbMariaUser, password=dbMariaPassword, database=dbMariaName)
	elif (dbType.lower() == "postgresql") or (dbType.lower() == "pgsql") or (dbType.lower() == "posgres") :
		conn = psycopg2.connect(host=dbPgHost, user=dbPgUser, password=dbPgPassword, database=dbPgName, port=dbPgPort)
	else:
		logger.critical("'{}' is not a supported database type!".format(dbType))
		quit()
except Exception as e:
	logger.critical("Can't connect to the database: {}".format(e))
	quit()


# Initialization of the Discord client
client = None

task_feed       	= None
task_feed_anilist	= None
task_gameplayed 	= None
task_thumbnail  	= None
