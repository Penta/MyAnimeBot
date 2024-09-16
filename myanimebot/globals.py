import logging
import os
import socket
from configparser import ConfigParser

import discord
import pytz
import feedparser
import mariadb
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

def get_env_var(name, default=None):
    return os.getenv(name, default)

CONFIG=config["MYANIMEBOT"]
logLevel = get_env_var("MYANIMEBOT_LOGLEVEL", CONFIG.get("logLevel", "INFO"))
dbHost = get_env_var("MYANIMEBOT_DBHOST", CONFIG.get("mariadb.host", "127.0.0.1"))
dbUser = get_env_var("MYANIMEBOT_DBUSER", CONFIG.get("mariadb.user", "myanimebot"))
dbPassword = get_env_var("MYANIMEBOT_DBPASSWORD", CONFIG.get("mariadb.password"))
dbName = get_env_var("MYANIMEBOT_DBNAME", CONFIG.get("mariadb.name", "myanimebot"))
dbSSLenabled = get_env_var("MYANIMEBOT_DBSSL", CONFIG.getboolean("mariadb.ssl", False))
dbSSLca = get_env_var("MYANIMEBOT_DBSSLCACERT", CONFIG.get("mariadb.ssl.ca"))
dbSSLcert = get_env_var("MYANIMEBOT_DBSSLCERT", CONFIG.get("mariadb.ssl.cert"))
dbSSLkey = get_env_var("MYANIMEBOT_DBSSLKEY", CONFIG.get("mariadb.ssl.key"))
logPath = get_env_var("MYANIMEBOT_LOGPATH", CONFIG.get("logPath", "myanimebot.log"))
timezone = pytz.timezone(get_env_var("MYANIMEBOT_TIMEZONE", CONFIG.get("timezone", "utc")))
secondMax = int(get_env_var("MYANIMEBOT_SECOND_MAX", CONFIG.getint("secondMax", 7200)))
token = get_env_var("MYANIMEBOT_TOKEN", CONFIG.get("token"))
prefix = get_env_var("MYANIMEBOT_PREFIX", CONFIG.get("prefix", "!mab"))
MYANIMELIST_SECONDS_BETWEEN_REQUESTS = int(get_env_var("MYANIMEBOT_MAL_REQUESTS", CONFIG.getint("myanimelist_seconds_between_requests", 2)))
iconBot = get_env_var("MYANIMEBOT_ICONBOT", CONFIG.get("iconBot", "http://myanimebot.pentou.eu/rsc/bot_avatar.jpg"))
ANILIST_SECONDS_BETWEEN_FETCHES = int(get_env_var("MYANIMEBOT_ANILIST_FETCHES", CONFIG.getint("anilist_seconds_between_fetches", 60)))
MAL_ICON_URL = get_env_var("MYANIMEBOT_MAL_ICON", CONFIG.get("iconMAL", "https://cdn.myanimelist.net/img/sp/icon/apple-touch-icon-256.png"))
ANILIST_ICON_URL = get_env_var("MYANIMEBOT_ANILIST_ICON", CONFIG.get("iconAniList", "https://anilist.co/img/icons/android-chrome-512x512.png"))
MAL_ENABLED = get_env_var("MYANIMEBOT_MAL_ENABLED", CONFIG.getboolean("mal_enabled", True))
ANI_ENABLED = get_env_var("MYANIMEBOT_ANI_ENABLED", CONFIG.getboolean("ani_enabled", True))
HEALTHCHECK_ENABLED = get_env_var("MYANIMEBOT_HEALTHCHECK_ENABLED", CONFIG.getboolean("healthcheck_enabled", False))
HEALTHCHECK_PORT = int(get_env_var("MYANIMEBOT_HEALTHCHECK_PORT", CONFIG.getint("healthcheck_port", 15200)))
HEALTHCHECK_IP = get_env_var("MYANIMEBOT_HEALTHCHECK_IP", CONFIG.get("healthcheck_ip", "0.0.0.0"))

SERVICE_ANILIST = "ani"
SERVICE_MAL = "mal"
MAL_URL = "https://myanimelist.net/"
MAL_PROFILE_URL = "https://myanimelist.net/profile/"
ANILIST_PROFILE_URL = "https://anilist.co/user/"
DB_USER_NAME = "mal_user"  # Nom de la colonne pour les noms d'utilisateur dans la table t_users

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
	if (dbSSLenabled) :
		conn = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName, ssl_ca=dbSSLca, ssl_cert=dbSSLcert, ssl_key=dbSSLkey)
	else :
		conn = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName)
except Exception as e:
	logger.critical("Can't connect to the database: " + str(e))
	quit()


# Initialization of the Discord client
client = None

task_feed       	= None
task_feed_anilist	= None
task_gameplayed 	= None
task_thumbnail  	= None
