#!/usr/bin/env python3
# Copyright Penta (c) 2018/2020 - Under BSD License - Based on feed2discord.py by Eric Eisenhart

# Compatible for Python 3.7.X
#
# Dependencies (for CentOS 7):
# curl -LsS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | sudo bash
# yum install gcc MariaDB-client MariaDB-common MariaDB-shared MariaDB-devel
# python3.7 -m pip install --upgrade pip
# pip3.7 install discord.py mariadb pytz feedparser python-dateutil asyncio html2text bs4 PyNaCL aiodns cchardet configparser
# TODO Remove all of that

# TODO MAL should not check AniList users

import asyncio
# Library import
import logging
import sys
import urllib.request
from configparser import ConfigParser
from datetime import datetime
from typing import List, Tuple

import aiohttp
import discord
import feedparser
from aiohttp.web_exceptions import HTTPError, HTTPNotModified
from dateutil.parser import parse as parse_datetime
from html2text import HTML2Text

# Our modules
import myanimebot.anilist as anilist
import myanimebot.globals as globals
import myanimebot.utils as utils
import myanimebot.myanimelist as myanimelist
from myanimebot.discord import send_embed_wrapper, build_embed


if not sys.version_info[:2] >= (3, 7):
	print("ERROR: Requires python 3.7 or newer.")
	exit(1)

	
# Main function that check the RSS feeds from MyAnimeList
async def background_check_feed(asyncioloop):
	globals.logger.info("Starting up background_check_feed")
	
	# We configure the http header
	http_headers = { "User-Agent": "MyAnimeBot Discord Bot v" + globals.VERSION, }
	
	await globals.client.wait_until_ready()
	
	globals.logger.debug("Discord client connected, unlocking background_check_feed...")
	
	while not globals.client.is_closed():
		try:
			db_user = globals.conn.cursor(buffered=True, dictionary=True)
			db_user.execute("SELECT mal_user, servers FROM t_users")
			data_user = db_user.fetchone()
		except Exception as e:
			globals.logger.critical("Database unavailable! (" + str(e) + ")")
			quit()

		while data_user is not None:
			user = utils.User(id=None,
								service_id=None,
								name=data_user[globals.DB_USER_NAME],
								servers=data_user["servers"].split(','))
			stop_boucle = 0
			feed_type = 1

			try:
				while stop_boucle == 0 :
					try:
						async with aiohttp.ClientSession() as httpclient:
							if feed_type == 1 :
								http_response = await httpclient.request("GET", "https://myanimelist.net/rss.php?type=rm&u=" + user.name, headers=http_headers)
								media = "manga"
							else : 
								http_response = await httpclient.request("GET", "https://myanimelist.net/rss.php?type=rw&u=" + user.name, headers=http_headers)
								media = "anime"
					except Exception as e:
						globals.logger.error("Error while loading RSS (" + str(feed_type) + ") of '" + user.name + "': " + str(e))
						break

					http_data = await http_response.read()
					feeds_data = feedparser.parse(http_data)
					
					for feed_data in feeds_data.entries:
						pubDateRaw = datetime.strptime(feed_data.published, '%a, %d %b %Y %H:%M:%S %z').astimezone(globals.timezone)
						DateTimezone = pubDateRaw.strftime("%z")[:3] + ':' + pubDateRaw.strftime("%z")[3:]
						pubDate = pubDateRaw.strftime("%Y-%m-%d %H:%M:%S")
						feed = myanimelist.build_feed_from_data(feed_data, user, None, pubDateRaw.timestamp(), feed_type)
						
						cursor = globals.conn.cursor(buffered=True)
						cursor.execute("SELECT published, title, url FROM t_feeds WHERE published=%s AND title=%s AND user=%s", [pubDate, feed.media.name, user.name])
						data = cursor.fetchone()

						if data is None:
							var = datetime.now(globals.timezone) - pubDateRaw
							
							globals.logger.debug(" - " + feed.media.name + ": " + str(var.total_seconds()))
						
							if var.total_seconds() < globals.secondMax:
								globals.logger.info(user.name + ": Item '" + feed.media.name + "' not seen, processing...")
								
								cursor.execute("SELECT thumbnail FROM t_animes WHERE guid=%s LIMIT 1", [feed.media.url]) # TODO Change that ?
								data_img = cursor.fetchone()
								
								if data_img is None:
									try:
										image = myanimelist.get_thumbnail(feed.media.url)
										
										globals.logger.info("First time seeing this " + media + ", adding thumbnail into database: " + image)
									except Exception as e:
										globals.logger.warning("Error while getting the thumbnail: " + str(e))
										image = ""
										
									cursor.execute("INSERT INTO t_animes (guid, title, thumbnail, found, discoverer, media) VALUES (%s, %s, %s, NOW(), %s, %s)", [feed.media.url, feed.media.name, image, user.name, media])
									globals.conn.commit()
								else: image = data_img[0]
								feed.media.image = image

								type = feed.description.partition(" - ")[0]

								cursor.execute("INSERT INTO t_feeds (published, title, url, user, found, type) VALUES (%s, %s, %s, %s, NOW(), %s)", (pubDate, feed.media.name, feed.media.url, user.name, type))
								globals.conn.commit()
								
								for server in user.servers:
									db_srv = globals.conn.cursor(buffered=True)
									db_srv.execute("SELECT channel FROM t_servers WHERE server = %s", [server])
									data_channel = db_srv.fetchone()
									
									while data_channel is not None:
										for channel in data_channel: await send_embed_wrapper(asyncioloop, channel, globals.client, build_embed(feed))
										
										data_channel = db_srv.fetchone()
					if feed_type == 1:
						feed_type = 0
						await asyncio.sleep(1)
					else:
						stop_boucle = 1
					
			except Exception as e:
				globals.logger.error("Error when parsing RSS for '" + user.name + "': " + str(e))
			
			await asyncio.sleep(1)

			data_user = db_user.fetchone()


async def fetch_activities_anilist():
	await anilist.check_new_activities()


@globals.client.event
async def on_ready():
	globals.logger.info("Logged in as " + globals.client.user.name + " (" + str(globals.client.user.id) + ")")

	globals.logger.info("Starting all tasks...")

	globals.task_feed = globals.client.loop.create_task(background_check_feed(globals.client.loop))
	globals.task_feed_anilist = globals.client.loop.create_task(anilist.background_check_feed(globals.client.loop))
	globals.task_thumbnail = globals.client.loop.create_task(update_thumbnail_catalog(globals.client.loop))
	globals.task_gameplayed = globals.client.loop.create_task(change_gameplayed(globals.client.loop))


@globals.client.event
async def on_error(event, *args, **kwargs):
    globals.logger.exception("Crap! An unknown Discord error occured...")


def build_info_cmd_message(users, server, channels, filters : List[utils.Service]) -> str:
	''' Build the corresponding message for the info command '''

	registered_channel = globals.client.get_channel(int(channels[0]["channel"]))

	# Store users
	mal_users = []
	anilist_users = []
	for user in users:
		# If user is part of the server, add it to the message
		if str(server.id) in user['servers'].split(','):
			try:
				user_service = utils.Service.from_str(user["service"])
				if user_service == utils.Service.MAL:
					mal_users.append(user[globals.DB_USER_NAME])
				elif user_service == utils.Service.ANILIST:
					anilist_users.append(user[globals.DB_USER_NAME])
			except NotImplementedError:
				pass # Nothing to do here

	if not mal_users and not anilist_users:
		return "No users registered on this server. Try to add one."
	else:
		message =  'Registered user(s) on **{}**\n\n'.format(server)
		if mal_users: # If not empty
			# Don't print if there is filters and MAL is not in them
			if not filters or (filters and utils.Service.MAL in filters): 
				message += '**MyAnimeList** users:\n'
				message += '```{}```\n'.format(', '.join(mal_users))
		if anilist_users: # If not empty
			# Don't print if there is filters and MAL is not in them
			if not filters or (filters and utils.Service.ANILIST in filters):
				message += '**AniList** users:\n'
				message += '```{}```\n'.format(', '.join(anilist_users))
		message += 'Assigned channel : **{}**'.format(registered_channel)
	return message


def get_service_filters_list(filters : str) -> List[utils.Service]:
	''' Creates and returns a service filter list from a comma-separated string '''

	filters_list = []
	for filter in filters.split(','):
		try:
			filters_list.append(utils.Service.from_str(filter))
		except NotImplementedError:
			pass # Ignore incorrect filter
	return filters_list


async def info_cmd(message, words):
	''' Processes the command "info" and sends a message '''

	# Get filters if available
	filters = []
	if (len(words) >= 3): # If filters are specified
		filters = get_service_filters_list(words[2])

	server = message.guild
	if utils.is_server_in_db(server.id) == False:
		 await message.channel.send("The server **{}** is not in our database.".format(server))
	else:
		users = utils.get_users()
		channels = utils.get_channels(server.id)
		if channels is None:
			await message.channel.send("No channel assigned for this bot on this server.")
		else:
			await message.channel.send(build_info_cmd_message(users, server, channels, filters))


def check_user_name_validity(user_name: str, service : utils.Service) -> Tuple[bool, str]:
	""" Check if user_name exists on a specific service.
		
		Returns:
			- bool: 	True if user_name exists
			- str:		Error string if the user does not exist
	"""

	if service == utils.Service.MAL:
		try:
			# Ping user profile to check validity
			urllib.request.urlopen('{}{}'.format(globals.MAL_PROFILE_URL, user_name))
		except urllib.error.HTTPError as e:
			if (e.code == 404): # URL profile not found
				return False, "User **{}** doesn't exist on MyAnimeList!".format(user_name)
			else:
				globals.logger.warning("HTTP Code {} while trying to add user '{}' and checking its validity.".format(e.code, user_name))
				return False, "An error occured when we checked this username on MyAnimeList, maybe the website is down?"
	elif service == utils.Service.ANILIST:
		is_user_valid = anilist.check_username_validity(user_name)
		if is_user_valid == False:
			globals.logger.warning("No results returned while trying to add user '{}' and checking its validity.".format(user_name))
			return False, "User **{}** doesn't exist on AniList!".format(user_name)
	return True, None


async def add_user_cmd(words, message):
	''' Processes the command "add" and add a user to fetch the data for '''

	# Check if command is valid
	if len(words) != 4:
		if (len(words) < 4):
			return await message.channel.send("Usage: {} add **{}**/**{}** **username**".format(globals.prefix, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
		return await message.channel.send("Too many arguments! You have to specify only one username.")

	try:
		service = utils.Service.from_str(words[2])
	except NotImplementedError:
		return await message.channel.send('Incorrect service. Use **"{}"** or **"{}"** for example'.format(globals.SERVICE_MAL, globals.SERVICE_ANILIST))
	user = words[3]
	server_id = str(message.guild.id)

	if(len(user) > 14):
		return await message.channel.send("Username too long!")

	try:
		# Check user validity
		is_valid, error_string = check_user_name_validity(user, service)
		if is_valid == False:
			return await message.channel.send(error_string)

		# Get user's servers
		user_servers = utils.get_user_servers(user, service)
		# User not present in database
		if user_servers is None: 
			utils.insert_user_into_db(user, service, server_id)
			return await message.channel.send("**{}** added to the database for the server **{}**.".format(user, str(message.guild)))
		else: # User present in database

			is_server_present = server_id in user_servers.split(',')
			if is_server_present == True: # The user already has registered this server
				return await message.channel.send("User **{}** is already registered in our database for this server!".format(user))
			else:
				new_servers = '{},{}'.format(user_servers, server_id)
				utils.update_user_servers_db(user, service, new_servers)					
				return await message.channel.send("**{}** added to the database for the server **{}**.".format(user, str(message.guild)))
	except Exception as e:
		globals.logger.warning("Error while adding user '{}' on server '{}': {}".format(user, message.guild, str(e)))
		return await message.channel.send("An unknown error occured while addind this user, the error has been logged.")


async def delete_user_cmd(words, message):
	''' Processes the command "delete" and remove a registered user '''

	# Check if command is valid
	if len(words) != 4:
		if (len(words) < 4):
			return await message.channel.send("Usage: {} delete **{}**/**{}** **username**".format(globals.prefix, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
		return await message.channel.send("Too many arguments! You have to specify only one username.")
	try:
		service = utils.Service.from_str(words[2])
	except NotImplementedError:
		return await message.channel.send('Incorrect service. Use **"{}"** or **"{}"** for example'.format(globals.SERVICE_MAL, globals.SERVICE_ANILIST))
	user = words[3]
	server_id = str(message.guild.id)
	
	user_servers = utils.get_user_servers(user, service)
	# If user is not present in the database
	if user_servers is None:
		return await message.channel.send("The user **" + user + "** is not in our database for this server!")

	# Else if present, update the servers for this user
	srv_string = utils.remove_server_from_servers(server_id, user_servers)
	
	if srv_string is None: # Server not present in the user's servers
		return await message.channel.send("The user **" + user + "** is not in our database for this server!")

	if srv_string == "":
		utils.delete_user_from_db(user, service)
	else:
		utils.update_user_servers_db(user, service, srv_string)

	return await message.channel.send("**" + user + "** deleted from the database for this server.")


@globals.client.event
async def on_message(message):
	if message.author == globals.client.user: return

	words = message.content.split(" ")
	author = str('{0.author.mention}'.format(message))

	# A user is trying to get help
	if words[0] == globals.prefix:
		if len(words) > 1:
			if words[1] == "ping":
				await message.channel.send("pong")
			
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
				await add_user_cmd(words, message)
				
			elif words[1] == "delete":
				await delete_user_cmd(words, message)
				
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
				await info_cmd(message, words)

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
					image = myanimelist.get_thumbnail(data[0])
						
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
        globals.task_feed_anilist.cancel()
        globals.task_thumbnail.cancel()
        globals.task_gameplayed.cancel()

    globals.logger.critical("Script halted.")

	# We close all the ressources
    globals.conn.close()
    globals.log_cursor.close()
    globals.log_conn.close()
