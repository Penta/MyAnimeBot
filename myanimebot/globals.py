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

CONFIG=config["MYANIMEBOT"]
logLevel=CONFIG.get("logLevel", "INFO")
dbHost=CONFIG.get("dbHost", "127.0.0.1")
dbUser=CONFIG.get("dbUser", "myanimebot")
dbPassword=CONFIG.get("dbPassword")
dbName=CONFIG.get("dbName", "myanimebot")
logPath=CONFIG.get("logPath", "myanimebot.log")
timezone=pytz.timezone(CONFIG.get("timezone", "utc"))
secondMax=CONFIG.getint("secondMax", 7200)
token=CONFIG.get("token")
prefix=CONFIG.get("prefix", "!mab")
delayMAL=CONFIG.get("delayMAL", "2")
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

# class that send logs to DB
class LogDBHandler(logging.Handler):
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

logger = logging.getLogger("myanimebot")
logger.setLevel(logLevel)

logging.getLogger('').addHandler(console)

# Script version
VERSION = "1.0.0a"

# The help message
HELP = 	"""**Here's some help for you:**
```
- here :
Type this command on the channel where you want to see the activity of the MAL profiles.

- stop :
Cancel the here command, no message will be displayed.

- add :
Followed by a username, add a MAL user into the database to be displayed on this server.
ex: add MyUser

- delete :
Followed by a username, remove a user from the database.
ex: delete MyUser

- group :
Specify a group that can use the add and delete commands.

- info :
Get the users already in the database for this server.

- about :
Get some information about this bot.
```"""

logger.info("Booting MyAnimeBot " + VERSION + "...")
logger.debug("DEBUG log: OK")

# feedparser.PREFERRED_XML_PARSERS.remove("drv_libxml2")

# Initialization of the database
try:
	# Main database connection
	conn = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName)
	
	# We initialize the logs into the DB.
	log_conn   = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName)
	log_cursor = log_conn.cursor()
	logdb = LogDBHandler(log_conn, log_cursor)
	logging.getLogger('').addHandler(logdb)
	
	logger.info("The database logger is running.")
except Exception as e:
	logger.critical("Can't connect to the database: " + str(e))
	quit()


# Initialization of the Discord client
client = discord.Client()

task_feed       	= None
task_feed_anilist	= None
task_gameplayed 	= None
task_thumbnail  	= None
