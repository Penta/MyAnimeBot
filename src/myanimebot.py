#!/usr/bin/env python3
# Copyright Penta (c) 2018/2020 - Under BSD License - Based on feed2discord.py by Eric Eisenhart

# Compatible for Python 3.7.X
#
# Dependencies (for CentOS 7):
# curl -LsS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | sudo bash
# yum install gcc MariaDB-client MariaDB-common MariaDB-shared MariaDB-devel
# python3.7 -m pip install --upgrade pip
# pip3.7 install discord.py mariadb pytz feedparser python-dateutil asyncio html2text bs4 PyNaCL aiodns cchardet configparser

# Library import
import logging
import os
import sys
import discord
import feedparser
import pytz
import aiohttp
import asyncio
import urllib.request
import mariadb
import string
import time
import socket
import requests

# Custom libraries
import globals
import anilist
import utils

from configparser import ConfigParser
from datetime import datetime
from dateutil.parser import parse as parse_datetime
from html2text import HTML2Text
from aiohttp.web_exceptions import HTTPError, HTTPNotModified

if not sys.version_info[:2] >= (3, 7):
	print("ERROR: Requires python 3.7 or newer.")
	exit(1)

# TODO Create a Feed class instead of sending a lot of parameters
def build_embed(user, item_title, item_link, item_description, pub_date, image, service: utils.Service):
	''' Build the embed message related to the anime's status '''

	# Get service
	if service == utils.Service.MAL:
		service_name = 'MyAnimeList'
		profile_url = "{}{}".format(globals.MAL_PROFILE_URL, user)
	elif service == utils.Service.ANILIST:
		service_name = 'AniList'
		profile_url = "{}{}".format(globals.ANILIST_PROFILE_URL, user)
	else:
		raise NotImplementedError('Unknown service {}'.format(service))
	description = "[{}]({})\n```{}```".format(utils.filter_name(item_title), item_link, item_description)
	profile_url_label = "{}'s {}".format(user, service_name)

	try:	
		embed = discord.Embed(colour=0xEED000,
								url=item_link,
								description=description,
								timestamp=pub_date.astimezone(pytz.timezone("utc")))
		embed.set_thumbnail(url=image)
		embed.set_author(name=profile_url_label, url=profile_url, icon_url=globals.iconMAL)
		embed.set_footer(text="MyAnimeBot", icon_url=globals.iconBot)
		
		return embed
	except Exception as e:
		globals.logger.error("Error when generating the message: " + str(e))
		return

# Function used to send the embed
async def send_embed_wrapper(asyncioloop, channelid, client, embed):
	channel = client.get_channel(int(channelid))
	
	try:
		await channel.send(embed=embed)
		globals.logger.info("Message sent in channel: " + channelid)
	except Exception as e:
		globals.logger.debug("Impossible to send a message on '" + channelid + "': " + str(e)) 
		return
	
# Main function that check the RSS feeds from MyAnimeList
async def background_check_feed(asyncioloop):
	globals.logger.info("Starting up background_check_feed")
	
	# We configure the http header
	http_headers = { "User-Agent": "MyAnimeBot Discord Bot v" + globals.VERSION, }
	
	await globals.client.wait_until_ready()
	
	globals.logger.debug("Discord client connected, unlocking background_check_feed...")
	
	while not globals.client.is_closed():
		try:
			db_user = globals.conn.cursor(buffered=True)
			db_user.execute("SELECT mal_user, servers FROM t_users")
			data_user = db_user.fetchone()
		except Exception as e:
			globals.logger.critical("Database unavailable! (" + str(e) + ")")
			quit()

		while data_user is not None:
			user=data_user[0]
			stop_boucle = 0
			feed_type = 1
			
			globals.logger.debug("checking user: " + user)
			
			try:
				while stop_boucle == 0 :
					try:
						async with aiohttp.ClientSession() as httpclient:
							if feed_type == 1 :
								http_response = await httpclient.request("GET", "https://myanimelist.net/rss.php?type=rm&u=" + user, headers=http_headers)
								media = "manga"
							else : 
								http_response = await httpclient.request("GET", "https://myanimelist.net/rss.php?type=rw&u=" + user, headers=http_headers)
								media = "anime"
					except Exception as e:
						globals.logger.error("Error while loading RSS (" + str(feed_type) + ") of '" + user + "': " + str(e))
						break

					http_data = await http_response.read()
					feed_data = feedparser.parse(http_data)
					
					for item in feed_data.entries:
						pubDateRaw = datetime.strptime(item.published, '%a, %d %b %Y %H:%M:%S %z').astimezone(globals.timezone)
						DateTimezone = pubDateRaw.strftime("%z")[:3] + ':' + pubDateRaw.strftime("%z")[3:]
						pubDate = pubDateRaw.strftime("%Y-%m-%d %H:%M:%S")
						
						cursor = globals.conn.cursor(buffered=True)
						cursor.execute("SELECT published, title, url FROM t_feeds WHERE published=%s AND title=%s AND user=%s", [pubDate, item.title, user])
						data = cursor.fetchone()

						if data is None:
							var = datetime.now(globals.timezone) - pubDateRaw
							
							globals.logger.debug(" - " + item.title + ": " + str(var.total_seconds()))
						
							if var.total_seconds() < globals.secondMax:
								globals.logger.info(user + ": Item '" + item.title + "' not seen, processing...")
								
								if item.description.startswith('-') :
									if feed_type == 1 :	item.description = "Re-Reading " + item.description
									else :				item.description = "Re-Watching " + item.description
								
								cursor.execute("SELECT thumbnail FROM t_animes WHERE guid=%s LIMIT 1", [item.guid])
								data_img = cursor.fetchone()
								
								if data_img is None:
									try:
										image = utils.getThumbnail(item.link)
										
										globals.logger.info("First time seeing this " + media + ", adding thumbnail into database: " + image)
									except Exception as e:
										globals.logger.warning("Error while getting the thumbnail: " + str(e))
										image = ""
										
									cursor.execute("INSERT INTO t_animes (guid, title, thumbnail, found, discoverer, media) VALUES (%s, %s, %s, NOW(), %s, %s)", [item.guid, item.title, image, user, media])
									globals.conn.commit()
								else: image = data_img[0]

								type = item.description.partition(" - ")[0]
								
								cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type) VALUES (%s, %s, %s, %s, NOW(), %s)", (pubDate, item.title, item.guid, user, type))
								globals.conn.commit()
								
								for server in data_user[1].split(","):
									db_srv = globals.conn.cursor(buffered=True)
									db_srv.execute("SELECT channel FROM t_servers WHERE server = %s", [server])
									data_channel = db_srv.fetchone()
									
									while data_channel is not None:
										for channel in data_channel: await send_embed_wrapper(asyncioloop, channel, globals.client, build_embed(user, item.title, item.link, item.description, pubDateRaw, image, utils.Service.MAL))
										
										data_channel = db_srv.fetchone()
					if feed_type == 1:
						feed_type = 0
						await asyncio.sleep(1)
					else:
						stop_boucle = 1
					
			except Exception as e:
				globals.logger.error("Error when parsing RSS for '" + user + "': " + str(e))
			
			await asyncio.sleep(1)

			data_user = db_user.fetchone()


async def fetch_activities_anilist():
	print("Fetching activities")

	feed = {'__typename': 'ListActivity', 'id': 150515141, 'type': 'ANIME_LIST', 'status': 'rewatched episode', 'progress': '10 - 12', 'isLocked': False, 'createdAt': 1608738377, 'user': {'id': 102213, 'name': 'lululekiddo'}, 'media': {'id': 5081, 'siteUrl': 'https://anilist.co/anime/5081', 'title': {'romaji': 'Bakemonogatari', 'english': 'Bakemonogatari'}}}

	await anilist.check_new_activities()


@globals.client.event
async def on_ready():
	globals.logger.info("Logged in as " + globals.client.user.name + " (" + str(globals.client.user.id) + ")")

	globals.logger.info("Starting all tasks...")

	task_feed = globals.client.loop.create_task(background_check_feed(globals.client.loop))
	task_thumbnail = globals.client.loop.create_task(update_thumbnail_catalog(globals.client.loop))
	task_gameplayed = globals.client.loop.create_task(change_gameplayed(globals.client.loop))


@globals.client.event
async def on_error(event, *args, **kwargs):
    globals.logger.exception("Crap! An unknown Discord error occured...")

@globals.client.event
async def on_message(message):
	if message.author == globals.client.user: return

	words = message.content.split(" ")
	author = str('{0.author.mention}'.format(message))

	# A user is trying to get help
	if words[0] == globals.prefix:
		if len(words) > 1:
			if words[1] == "ping": await message.channel.send("pong")
			
			elif words[1] == "here":
				if message.author.guild_permissions.administrator:
					cursor = globals.conn.cursor(buffered=True)
					cursor.execute("SELECT server, channel FROM t_servers WHERE server=%s", [str(message.guild.id)])
					data = cursor.fetchone()
					
					if data is None:
						cursor.execute("INSERT INTO t_servers (server, channel) VALUES (%s,%s)", [str(message.guild.id), str(message.channel.id)])
						globals.conn.commit()
						
						await message.channel.send("Channel **" + str(message.channel) + "** configured for **" + str(message.guild) + "**.")
					else:
						if(data[1] == str(message.channel.id)): await message.channel.send("Channel **" + str(message.channel) + "** already in use for this server.")
						else:
							cursor.execute("UPDATE t_servers SET channel = %s WHERE server = %s", [str(message.channel.id), str(message.guild.id)])
							globals.conn.commit()
							
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
								
								cursor = globals.conn.cursor(buffered=True)
								cursor.execute("SELECT servers FROM t_users WHERE LOWER(mal_user)=%s", [user.lower()])
								data = cursor.fetchone()

								if data is None:
									cursor.execute("INSERT INTO t_users (mal_user, servers) VALUES (%s, %s)", [user, str(message.guild.id)])
									globals.conn.commit()
									
									await message.channel.send("**" + user + "** added to the database for the server **" + str(message.guild) + "**.")
								else:
									var = 0
									
									for server in data[0].split(","):
										if (server == str(message.guild.id)): var = 1
									
									if (var == 1):
										await message.channel.send("User **" + user + "** already in our database for this server!")
									else:
										cursor.execute("UPDATE t_users SET servers = %s WHERE LOWER(mal_user) = %s", [data[0] + "," + str(message.guild.id), user.lower()])
										globals.conn.commit()
										
										await message.channel.send("**" + user + "** added to the database for the server **" + str(message.guild) + "**.")
										
								cursor.close()
							except urllib.error.HTTPError as e:
								if (e.code == 404): await message.channel.send("User **" + user + "** doesn't exist on MyAnimeList!")
								else:
									await message.channel.send("An error occured when we checked this username on MyAnimeList, maybe the website is down?")
									globals.logger.warning("HTTP Code " + str(e.code) + " while checking to add for the new user '" + user + "'")
							except Exception as e:
								await message.channel.send("An unknown error occured while addind this user, the error has been logged.")
								globals.logger.warning("Error while adding user '" + user + "' on server '" + message.guild + "': " + str(e))
						else: await message.channel.send("Username too long!")
					else: await message.channel.send("Too many arguments! You have to specify only one username.")
				else: await message.channel.send("You have to specify a **MyAnimeList** username!")
				
			elif words[1] == "delete":
				if len(words) > 2:
					if (len(words) == 3):
						user = words[2]
						
						cursor = globals.conn.cursor(buffered=True)
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
								globals.conn.commit()
								
								await message.channel.send("**" + user + "** deleted from the database for this server.")
							else: await message.channel.send("The user **" + user + "** is not in our database for this server!")
						else: await message.channel.send("The user **" + user + "** is not in our database for this server!")
			
						cursor.close()
					else: await message.channel.send("Too many arguments! You have to specify only one username.")
				else: await message.channel.send("You have to specify a **MyAnimeList** username!")
				
			elif words[1] == "stop":
				if message.author.guild_permissions.administrator:
					if (len(words) == 2):
						cursor = globals.conn.cursor(buffered=True)
						cursor.execute("SELECT server FROM t_servers WHERE server=%s", [str(message.guild.id)])
						data = cursor.fetchone()
					
						if data is None: await globals.client.send_message(message.channel, "The server **" + str(message.guild) + "** is not in our database.")
						else:
							cursor.execute("DELETE FROM t_servers WHERE server = %s", [message.guild.id])
							globals.conn.commit()
							await message.channel.send("Server **" + str(message.guild) + "** deleted from our database.")
						
						cursor.close()
					else: await message.channel.send("Too many arguments! Only type *stop* if you want to stop this bot on **" + message.guild + "**")
				else: await message.channel.send("Only server's admins can use this command!")
				
			elif words[1] == "info":
				cursor = globals.conn.cursor(buffered=True)
				cursor.execute("SELECT server FROM t_servers WHERE server=%s", [str(message.guild.id)])
				data = cursor.fetchone()
				
				if data is None: await message.channel.send("The server **" + str(message.guild) + "** is not in our database.")
				else:
					user = ""
					cursor = globals.conn.cursor(buffered=True)
					cursor.execute("SELECT mal_user, servers FROM t_users")
					data = cursor.fetchone()
					
					cursor_channel = globals.conn.cursor(buffered=True)
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
						else: await message.channel.send("Here's the user(s) in the **" + str(message.guild) + "**'s server:\n```" + user + "```\nAssigned channel: **" + str(globals.client.get_channel(int(data_channel[0]))) + "**")

					cursor.close()
					cursor_channel.close()
			elif words[1] == "about": await message.channel.send(embed=discord.Embed(colour=0x777777, title="MyAnimeBot version " + globals.VERSION + " by Penta", description="This bot check the MyAnimeList's RSS for each user specified, and send a message if there is something new.\nMore help with the **!malbot help** command.\n\nAdd me on steam: http://steamcommunity.com/id/Penta_Pingouin").set_thumbnail(url="https://cdn.discordapp.com/avatars/415474467033317376/2d847944aab2104923c18863a41647da.jpg?size=64"))
			
			elif words[1] == "help": await message.channel.send(globals.HELP)
			
			elif words[1] == "top":
				if len(words) == 2:
					try:
						cursor = globals.conn.cursor(buffered=True)
						cursor.execute("SELECT * FROM v_Top")
						data = cursor.fetchone()
						
						if data is None: await message.channel.send("It seems that there is no statistics... (what happened?!)")
						else:
							topText = "**__Here is the global statistics of this bot:__**\n\n"
							
							while data is not None:
								topText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
									
								data = cursor.fetchone()
								
							cursor = globals.conn.cursor(buffered=True)
							cursor.execute("SELECT * FROM v_TotalFeeds")
							data = cursor.fetchone()
							
							topText += "\n***Total user entry***: " + str(data[0])
							
							cursor = globals.conn.cursor(buffered=True)
							cursor.execute("SELECT * FROM v_TotalAnimes")
							data = cursor.fetchone()
							
							topText += "\n***Total unique manga/anime***: " + str(data[0])
							
							await message.channel.send(topText)
						
						cursor.close()
					except Exception as e:
						globals.logger.warning("An error occured while displaying the global top: " + str(e))
						await message.channel.send("Unable to reply to your request at the moment...")
				elif len(words) > 2:
					keyword = str(' '.join(words[2:]))
					globals.logger.info("Displaying the global top for the keyword: " + keyword)
					
					try:
						cursor = globals.conn.cursor(buffered=True)
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
						globals.logger.warning("An error occured while displaying the global top for keyword '" + keyword + "': " + str(e))
						await message.channel.send("Unable to reply to your request at the moment...")
			
			elif words[1] == "group":
				if len(words) > 2:
					if message.author.guild_permissions.administrator:
						group = words[2]
						await message.channel.send("admin OK")
					else: await message.channel.send("Only server's admins can use this command!")
				else:
					await message.channel.send("You have to specify a group!")

			elif words[1] == "fetch-debug":
				await fetch_activities_anilist()

	# If mentioned
	elif globals.client.user in message.mentions:
		await message.channel.send(":heart:")

# Get a random anime name and change the bot's activity
async def change_gameplayed(asyncioloop):
	globals.logger.info("Starting up change_gameplayed")
	
	await globals.client.wait_until_ready()
	await asyncio.sleep(1)

	while not globals.client.is_closed():
		# Get a random anime name from the users' list
		cursor = globals.conn.cursor(buffered=True)
		cursor.execute("SELECT title FROM t_animes ORDER BY RAND() LIMIT 1")
		data = cursor.fetchone()
		anime = utils.truncate_end_show(data[0])
		
		# Try to change the bot's activity
		try:
			if data is not None: await globals.client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=anime))
		except Exception as e:
			globals.logger.warning("An error occured while changing the displayed anime title: " + str(e))
			
		cursor.close()
		# Do it every minute
		await asyncio.sleep(60)

async def update_thumbnail_catalog(asyncioloop):
	globals.logger.info("Starting up update_thumbnail_catalog")
	
	while not globals.client.is_closed():
		await asyncio.sleep(43200)
		
		globals.logger.info("Automatic check of the thumbnail database on going...")
		reload = 0
		
		cursor = globals.conn.cursor(buffered=True)
		cursor.execute("SELECT guid, title, thumbnail FROM t_animes")
		data = cursor.fetchone()

		while data is not None:
			try:
				if (data[2] != "") : urllib.request.urlopen(data[2])
				else: reload = 1
			except urllib.error.HTTPError as e:
				globals.logger.warning("HTTP Error while getting the current thumbnail of '" + str(data[1]) + "': " + str(e))
				reload = 1
			except Exception as e:
				globals.logger.debug("Error while getting the current thumbnail of '" + str(data[1]) + "': " + str(e))
			
			if (reload == 1) :
				try:
					image = utils.getThumbnail(data[0])
						
					cursor.execute("UPDATE t_animes SET thumbnail = %s WHERE guid = %s", [image, data[0]])
					globals.conn.commit()
						
					globals.logger.info("Updated thumbnail found for \"" + str(data[1]) + "\": %s", image)
				except Exception as e:
					globals.logger.warning("Error while downloading updated thumbnail for '" + str(data[1]) + "': " + str(e))

			await asyncio.sleep(3)
			data = cursor.fetchone()

		cursor.close()

		globals.logger.info("Thumbnail database checked.")
	
# Starting main function	
if __name__ == "__main__":
    try:
        globals.client.run(globals.token)
    except:
        logging.info("Closing all tasks...")
        globals.task_feed.cancel()
        globals.task_thumbnail.cancel()
        globals.task_gameplayed.cancel()

    globals.logger.critical("Script halted.")

	# We close all the ressources
    globals.conn.close()
    globals.log_cursor.close()
    globals.log_conn.close()
