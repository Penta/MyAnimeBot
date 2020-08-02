#!/usr/bin/env python3
# Copyright Penta (c) 2018/2020 - Under BSD License - Based on feed2discord.py by Eric Eisenhart

# Compatible for Python 3.7.X
#
# Dependencies (for CentOS 7):
# yum install python3 mariadb-devel gcc python3-devel
# python3.7 -m pip install --upgrade pip
# pip3.7 install discord.py mysql pytz feedparser python-dateutil asyncio html2text bs4 PyNaCL aiodns cchardet configparser
# pip3.7 install mysql.connector

# Library import
import logging
import os
import re
import sys
import discord
import feedparser
import pytz
import aiohttp
import asyncio
import urllib.request
import mysql.connector as mariadb
import string
import time
import socket

from configparser import ConfigParser
from datetime import datetime
from dateutil.parser import parse as parse_datetime
from html2text import HTML2Text
from aiohttp.web_exceptions import HTTPError, HTTPNotModified
from bs4 import BeautifulSoup

if not sys.version_info[:2] >= (3, 7):
	print("ERROR: Requires python 3.7 or newer.")
	exit(1)

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
timezone=pytz.timezone(CONFIG.get("timezone", "utc"))
secondMax=CONFIG.getint("secondMax", 7200)
token=CONFIG.get("token")

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
			print (str(self.log_msg))
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
VERSION = "0.9.6.1"

# The help message
HELP = 	"""**Here's some help for you:**
```
- here :
Type this command on the channel where you want to see the activity of the MAL profiles.

- stop :
Cancel the here command, no message will be displayed.

- add :
Followed by a username, add a MAL user into the database to be displayed on this server.
ex: !malbot add MyUser

- delete :
Followed by a username, remove a user from the database.
ex: !malbot delete MyUser

- group :
Specify a group that can use the add and delete commands.

- info :
Get the users already in the database for this server.

- about :
Get some information about this bot.
```"""

logger.info("Booting MyAnimeBot " + VERSION + "...")
logger.debug("DEBUG log: OK")

# Initialization of the web client
httpclient = aiohttp.ClientSession()

feedparser.PREFERRED_XML_PARSERS.remove("drv_libxml2")

# Initialization of the database
try:
	# Main database connection
	conn = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName, buffered=True)
	
	# We initialize the logs into the DB.
	log_conn   = mariadb.connect(host=dbHost, user=dbUser, password=dbPassword, database=dbName, buffered=True)
	log_cursor = log_conn.cursor()
	logdb = LogDBHandler(log_conn, log_cursor)
	logging.getLogger('').addHandler(logdb)
	
	logger.info("The database logger is running.")
except Exception as e:
	logger.critical("Can't connect to the database: " + str(e))
	
	httpclient.close()
	quit()

# Initialization of the Discord client
client = discord.Client()

# Initialization of the thread handler
loop = asyncio.get_event_loop()

task_feed       = None
task_gameplayed = None
task_thumbnail  = None

# Function used to make the embed message related to the animes status
def build_embed(user, item, channel, pubDate, image):
	try:	
		embed = discord.Embed(colour=0xEED000, url=item.link, description="[" + filter_name(item.title) + "](" + item.link + ")\n```" + item.description + "```", timestamp=pubDate.astimezone(pytz.timezone("utc")))
		embed.set_thumbnail(url=image)
		embed.set_author(name=user + "'s MyAnimeList", url="https://myanimelist.net/profile/" + user, icon_url="http://myanimebot.pentou.eu/rsc/mal_icon_small.jpg")
		embed.set_footer(text="MyAnimeBot", icon_url="https://cdn.discordapp.com/avatars/415474467033317376/02609b6e371821e42ba7448c259edf40.jpg?size=32")
		
		return embed
	except Exception as e:
		logger.error("Error when generating the message: " + str(e))
		return

# Function used to send the embed
@asyncio.coroutine
def send_embed_wrapper(asyncioloop, channelid, client, embed):
	channel = client.get_channel(int(channelid))
	
	try:
		yield from channel.send(embed=embed)
		logger.info("Message sent in channel: " + channelid)
	except Exception as e:
		logger.debug("Impossible to send a message on '" + channelid + "': " + str(e)) 
		return

def filter_name(name):
	name = name.replace("♥", "\♥")
	name = name.replace("♀", "\♀")
	name = name.replace("♂", "\♂")
	name = name.replace("♪", "\♪")
	name = name.replace("☆", "\☆")
	return name
		
# Main function that check the RSS feeds from MyAnimeList
@asyncio.coroutine
def background_check_feed(asyncioloop):
	logger.info("Starting up background_check_feed")
	
	# We configure the http header
	http_headers = { "User-Agent": "MyAnimeBot Discord Bot v" + VERSION, }
	
	yield from client.wait_until_ready()
	
	logger.debug("Discord client connected, unlocking background_check_feed...")
	
	while not client.is_closed():
		try:
			db_user = conn.cursor(buffered=True)
			db_user.execute("SELECT mal_user, servers FROM t_users")
			data_user = db_user.fetchone()
		except Exception as e:
			logger.critical("Database unavailable! (" + str(e) + ")")
			quit()

		while data_user is not None:
			user=data_user[0]
			stop_boucle = 0
			feed_type = 1
			
			logger.debug("checking user: " + user)
			
			try:
				while stop_boucle == 0 :
					try:
						if feed_type == 1 :
							http_response = yield from httpclient.request("GET", "https://myanimelist.net/rss.php?type=rm&u=" + user, headers=http_headers)
							media = "manga"
						else : 
							http_response = yield from httpclient.request("GET", "https://myanimelist.net/rss.php?type=rw&u=" + user, headers=http_headers)
							media = "anime"
					except Exception as e:
						logger.error("Error while loading RSS (" + str(feed_type) + ") of '" + user + "': " + str(e))
						break

					http_data = yield from http_response.read()
					feed_data = feedparser.parse(http_data)
					
					http_response.close()

					for item in feed_data.entries:
						pubDateRaw = datetime.strptime(item.published, '%a, %d %b %Y %H:%M:%S %z').astimezone(timezone)
						DateTimezone = pubDateRaw.strftime("%z")[:3] + ':' + pubDateRaw.strftime("%z")[3:]
						pubDate = pubDateRaw.strftime("%Y-%m-%d %H:%M:%S")
						
						cursor = conn.cursor(buffered=True)
						cursor.execute("SELECT published, title, url FROM t_feeds WHERE published=%s AND title=%s AND user=%s", [pubDate, item.title, user])
						data = cursor.fetchone()

						if data is None:
							var = datetime.now(timezone) - pubDateRaw
							
							logger.debug(" - " + item.title + ": " + str(var.total_seconds()))
						
							if var.total_seconds() < secondMax:
								logger.info(user + ": Item '" + item.title + "' not seen, processing...")
								
								if item.description.startswith('-') :
									if feed_type == 1 :	item.description = "Re-Reading " + item.description
									else :				item.description = "Re-Watching " + item.description
								
								cursor.execute("SELECT thumbnail FROM t_animes WHERE guid=%s LIMIT 1", [item.guid])
								data_img = cursor.fetchone()
								
								if data_img is None:
									try:
										image = getThumbnail(item.link)
										
										logger.info("First time seeing this " + media + ", adding thumbnail into database: " + image)
									except Exception as e:
										logger.warning("Error while getting the thumbnail: " + str(e))
										image = ""
										
									cursor.execute("INSERT INTO t_animes (guid, title, thumbnail, found, discoverer, media) VALUES (%s, %s, %s, NOW(), %s, %s)", [item.guid, item.title, image, user, media])
									conn.commit()
								else: image = data_img[0]

								type = item.description.partition(" - ")[0]
								
								cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type) VALUES (%s, %s, %s, %s, NOW(), %s)", (pubDate, item.title, item.guid, user, type))
								conn.commit()
								
								for server in data_user[1].split(","):
									db_srv = conn.cursor(buffered=True)
									db_srv.execute("SELECT channel FROM t_servers WHERE server = %s", [server])
									data_channel = db_srv.fetchone()
									
									while data_channel is not None:
										for channel in data_channel: yield from send_embed_wrapper(asyncioloop, channel, client, build_embed(user, item, channel, pubDateRaw, image))
										
										data_channel = db_srv.fetchone()
					if feed_type == 1:
						feed_type = 0
						yield from asyncio.sleep(1)
					else:
						stop_boucle = 1
					
			except Exception as e:
				logger.error("Error when parsing RSS for '" + user + "': " + str(e))
			
			yield from asyncio.sleep(1)

			data_user = db_user.fetchone()

@client.event
async def on_ready():
	logger.info("Logged in as " + client.user.name + " (" + str(client.user.id) + ")")

@client.event
async def on_error(event, *args, **kwargs):
    logger.exception("Crap! An unknown Discord error occured...")

def getThumbnail(urlParam):
	url = "/".join((urlParam).split("/")[:5])
	
	websource = urllib.request.urlopen(url)
	soup = BeautifulSoup(websource.read(), "html.parser")
	image = re.search("(?P<url>https?://[^\s]+)", str(soup.find("img", {"itemprop": "image"}))).group("url")
	thumbnail = "".join(image.split('"')[:1]).replace('"','');
	
	return thumbnail

def main():
	logger.info("Starting all tasks...")

	try:
		task_feed = loop.create_task(background_check_feed(loop))
		task_thumbnail = loop.create_task(update_thumbnail_catalog(loop))
		task_gameplayed = loop.create_task(change_gameplayed(loop))
	
		client.run(token)
	except:
		logging.info("Closing all tasks...")
		
		task_feed.cancel()
		task_thumbnail.cancel()
		task_gameplayed.cancel()
		
		loop.run_until_complete(client.close())
	finally:
		loop.close()

@client.event
async def on_message(message):
	if message.author == client.user: return

	words = message.content.split(" ")
	author = str('{0.author.mention}'.format(message))

	if words[0] == "!malbot":
		if len(words) > 1:
			if words[1] == "ping": await message.channel.send("pong")
			
			elif words[1] == "here":
				if message.author.guild_permissions.administrator:
					cursor = conn.cursor(buffered=True)
					cursor.execute("SELECT server, channel FROM t_servers WHERE server=%s", [str(message.guild.id)])
					data = cursor.fetchone()
					
					if data is None:
						cursor.execute("INSERT INTO t_servers (server, channel) VALUES (%s,%s)", [str(message.guild.id), str(message.channel.id)])
						conn.commit()
						
						await message.channel.send("Channel **" + str(message.channel) + "** configured for **" + str(message.guild) + "**.")
					else:
						if(data[1] == str(message.channel.id)): await message.channel.send("Channel **" + str(message.channel) + "** already in use for this server.")
						else:
							cursor.execute("UPDATE t_servers SET channel = %s WHERE server = %s", [str(message.channel.id), str(message.guild.id)])
							conn.commit()
							
							await message.channel.send("Channel updated to: **" + str(message.channel) + "**.")
							
					cursor.close()
				else: await message.channel.send("Only server's admins can use this command!")
				
			elif words[1] == "add":
				if len(words) > 2:
					if (len(words) == 3):
						user = words[2]
						
						if(len(user) < 15):
							try:
								urllib.request.urlopen('https://myanimelist.net/profile/' + user)
								
								cursor = conn.cursor(buffered=True)
								cursor.execute("SELECT servers FROM t_users WHERE LOWER(mal_user)=%s", [user.lower()])
								data = cursor.fetchone()

								if data is None:
									cursor.execute("INSERT INTO t_users (mal_user, servers) VALUES (%s, %s)", [user, str(message.guild.id)])
									conn.commit()
									
									await message.channel.send("**" + user + "** added to the database for the server **" + str(message.guild) + "**.")
								else:
									var = 0
									
									for server in data[0].split(","):
										if (server == str(message.guild.id)): var = 1
									
									if (var == 1):
										await message.channel.send("User **" + user + "** already in our database for this server!")
									else:
										cursor.execute("UPDATE t_users SET servers = %s WHERE LOWER(mal_user) = %s", [data[0] + "," + str(message.guild.id), user.lower()])
										conn.commit()
										
										await message.channel.send("**" + user + "** added to the database for the server **" + str(message.guild) + "**.")
										
								cursor.close()
							except urllib.error.HTTPError as e:
								if (e.code == 404): await message.channel.send("User **" + user + "** doesn't exist on MyAnimeList!")
								else:
									await message.channel.send("An error occured when we checked this username on MyAnimeList, maybe the website is down?")
									logger.warning("HTTP Code " + str(e.code) + " while checking to add for the new user '" + user + "'")
							except Exception as e:
								await message.channel.send("An unknown error occured while addind this user, the error has been logged.")
								logger.warning("Error while adding user '" + user + "' on server '" + message.guild + "': " + str(e))
						else: await message.channel.send("Username too long!")
					else: await message.channel.send("Too many arguments! You have to specify only one username.")
				else: await message.channel.send("You have to specify a **MyAnimeList** username!")
				
			elif words[1] == "delete":
				if len(words) > 2:
					if (len(words) == 3):
						user = words[2]
						
						cursor = conn.cursor(buffered=True)
						cursor.execute("SELECT servers FROM t_users WHERE LOWER(mal_user)=%s", [user.lower()])
						data = cursor.fetchone()
						
						if data is not None:
							srv_string = ""
							present = 0
							
							for server in data[0].split(","):
								if server != str(message.guild.id):
									if srv_string == "": srv_string = server
									else: srv_string += "," + server
								else: present = 1
							
							if present == 1:
								if srv_string == "": cursor.execute("DELETE FROM t_users WHERE LOWER(mal_user) = %s", [user.lower()])
								else: cursor.execute("UPDATE t_users SET servers = %s WHERE LOWER(mal_user) = %s", [srv_string, user.lower()])
								conn.commit()
								
								await message.channel.send("**" + user + "** deleted from the database for this server.")
							else: await message.channel.send("The user **" + user + "** is not in our database for this server!")
						else: await message.channel.send("The user **" + user + "** is not in our database for this server!")
			
						cursor.close()
					else: await message.channel.send("Too many arguments! You have to specify only one username.")
				else: await message.channel.send("You have to specify a **MyAnimeList** username!")
				
			elif words[1] == "stop":
				if message.author.guild_permissions.administrator:
					if (len(words) == 2):
						cursor = conn.cursor(buffered=True)
						cursor.execute("SELECT server FROM t_servers WHERE server=%s", [str(message.guild.id)])
						data = cursor.fetchone()
					
						if data is None: await client.send_message(message.channel, "The server **" + str(message.guild) + "** is not in our database.")
						else:
							cursor.execute("DELETE FROM t_servers WHERE server = %s", [message.guild.id])
							conn.commit()
							await message.channel.send("Server **" + str(message.guild) + "** deleted from our database.")
						
						cursor.close()
					else: await message.channel.send("Too many arguments! Only type *stop* if you want to stop this bot on **" + message.guild + "**")
				else: await message.channel.send("Only server's admins can use this command!")
				
			elif words[1] == "info":
				cursor = conn.cursor(buffered=True)
				cursor.execute("SELECT server FROM t_servers WHERE server=%s", [str(message.guild.id)])
				data = cursor.fetchone()
				
				if data is None: await message.channel.send("The server **" + str(message.guild) + "** is not in our database.")
				else:
					user = ""
					cursor = conn.cursor(buffered=True)
					cursor.execute("SELECT mal_user, servers FROM t_users")
					data = cursor.fetchone()
					
					cursor_channel = conn.cursor(buffered=True)
					cursor_channel.execute("SELECT channel FROM t_servers WHERE server=%s", [str(message.guild.id)])
					data_channel = cursor_channel.fetchone()
					
					if data_channel is None: await message.channel.send("No channel assigned for this bot in this server.")
					else:
						while data is not None:
							if (str(message.guild.id) in data[1].split(",")):
								if (user == ""): user = data[0]
								else: user += ", " + data[0]
						
							data = cursor.fetchone()
						
						if (user == ""): await message.channel.send("No user in this server.")
						else: await message.channel.send("Here's the user(s) in the **" + str(message.guild) + "**'s server:\n```" + user + "```\nAssigned channel: **" + str(client.get_channel(int(data_channel[0]))) + "**")

					cursor.close()
					cursor_channel.close()
			elif words[1] == "about": await message.channel.send(embed=discord.Embed(colour=0x777777, title="MyAnimeBot version " + VERSION + " by Penta", description="This bot check the MyAnimeList's RSS for each user specified, and send a message if there is something new.\nMore help with the **!malbot help** command.\n\nAdd me on steam: http://steamcommunity.com/id/Penta_Pingouin").set_thumbnail(url="https://cdn.discordapp.com/avatars/415474467033317376/2d847944aab2104923c18863a41647da.jpg?size=64"))
			
			elif words[1] == "help": await message.channel.send(HELP)
			
			elif words[1] == "top":
				if len(words) == 2:
					try:
						cursor = conn.cursor(buffered=True)
						cursor.execute("SELECT * FROM v_Top")
						data = cursor.fetchone()
						
						if data is None: await message.channel.send("It seems that there is no statistics... (what happened?!)")
						else:
							topText = "**__Here is the global statistics of this bot:__**\n\n"
							
							while data is not None:
								topText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
									
								data = cursor.fetchone()
								
							cursor = conn.cursor(buffered=True)
							cursor.execute("SELECT * FROM v_TotalFeeds")
							data = cursor.fetchone()
							
							topText += "\n***Total user entry***: " + str(data[0])
							
							cursor = conn.cursor(buffered=True)
							cursor.execute("SELECT * FROM v_TotalAnimes")
							data = cursor.fetchone()
							
							topText += "\n***Total unique manga/anime***: " + str(data[0])
							
							await message.channel.send(topText)
						
						cursor.close()
					except Exception as e:
						logger.warning("An error occured while displaying the global top: " + str(e))
						await message.channel.send("Unable to reply to your request at the moment...")
				elif len(words) > 2:
					keyword = str(' '.join(words[2:]))
					logger.info("Displaying the global top for the keyword: " + keyword)
					
					try:
						cursor = conn.cursor(buffered=True)
						cursor.callproc('sp_UsersPerKeyword', [str(keyword), '20'])
						for result in cursor.stored_results():
							data = result.fetchone()
							
							if data is None: await message.channel.send("It seems that there is no statistics for the keyword **" + keyword + "**.")
							else:
								topKeyText = "**__Here is the statistics for the keyword " + keyword + ":__**\n\n"
								
								while data is not None:
									topKeyText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
										
									data = result.fetchone()
									
								await message.channel.send(topKeyText)
							
						cursor.close()
					except Exception as e:
						logger.warning("An error occured while displaying the global top for keyword '" + keyword + "': " + str(e))
						await message.channel.send("Unable to reply to your request at the moment...")
			
			elif words[1] == "group":
				if len(words) > 2:
					if message.author.guild_permissions.administrator:
						group = words[2]
						await message.channel.send("admin OK")
					else: await message.channel.send("Only server's admins can use this command!")
				else:
					await message.channel.send("You have to specify a group!")
		
	elif client.user in message.mentions:
		await message.channel.send(":heart:")

@asyncio.coroutine	
def change_gameplayed(asyncioloop):
	logger.info("Starting up change_gameplayed")
	
	yield from client.wait_until_ready()
	yield from asyncio.sleep(1)

	while not client.is_closed():
		cursor = conn.cursor(buffered=True)
		cursor.execute("SELECT title FROM t_animes ORDER BY RAND() LIMIT 1")
		data = cursor.fetchone()
		anime = data[0]
		
		if anime.endswith('- TV'): anime = anime[:-5]
		elif anime.endswith('- Movie'): anime = anime[:-8]
		elif anime.endswith('- Special'): anime = anime[:-10]
		elif anime.endswith('- OVA'): anime = anime[:-6]
		elif anime.endswith('- ONA'): anime = anime[:-6]
		elif anime.endswith('- Manga'): anime = anime[:-8]
		elif anime.endswith('- Manhua'): anime = anime[:-9]
		elif anime.endswith('- Manhwa'): anime = anime[:-9]
		elif anime.endswith('- Novel'): anime = anime[:-8]
		elif anime.endswith('- One-Shot'): anime = anime[:-11]
		elif anime.endswith('- Doujinshi'): anime = anime[:-12]
		elif anime.endswith('- Music'): anime = anime[:-8]
		elif anime.endswith('- OEL'): anime = anime[:-6]
		elif anime.endswith('- Unknown'): anime = anime[:-10]
		
		try:
			if data is not None: yield from client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=anime))
		except Exception as e:
			logger.warning("An error occured while changing the displayed anime title: " + str(e))
			
		cursor.close()
		
		yield from asyncio.sleep(60)

@asyncio.coroutine	
def update_thumbnail_catalog(asyncioloop):
	logger.info("Starting up update_thumbnail_catalog")
	
	while not client.is_closed():
		yield from asyncio.sleep(43200)
		
		logger.info("Automatic check of the thumbnail database on going...")
		reload = 0
		
		cursor = conn.cursor(buffered=True)
		cursor.execute("SELECT guid, title, thumbnail FROM t_animes")
		data = cursor.fetchone()

		while data is not None:
			try:
				if (data[2] != "") : urllib.request.urlopen(data[2])
				else: reload = 1
			except urllib.error.HTTPError as e:
				logger.warning("HTTP Error while getting the current thumbnail of '" + str(data[1]) + "': " + str(e))
				reload = 1
			except Exception as e:
				logger.debug("Error while getting the current thumbnail of '" + str(data[1]) + "': " + str(e))
			
			if (reload == 1) :
				try:
					image = getThumbnail(data[0])
						
					cursor.execute("UPDATE t_animes SET thumbnail = %s WHERE guid = %s", [image, data[0]])
					conn.commit()
						
					logger.info("Updated thumbnail found for \"" + str(data[1]) + "\": %s", image)
				except Exception as e:
					logger.warning("Error while downloading updated thumbnail for '" + str(data[1]) + "': " + str(e))

			yield from asyncio.sleep(3)
			data = cursor.fetchone()

		cursor.close()

		logger.info("Thumbnail database checked.")
	
# Starting main function	
if __name__ == "__main__":
	main()

	logger.critical("Script halted.")
	
	# We close all the ressources
	conn.close()
	log_cursor.close()
	log_conn.close()
	httpclient.close()
	loop.stop()
	loop.close()
