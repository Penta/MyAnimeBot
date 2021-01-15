import discord
import urllib
import datetime

from typing import List, Tuple

import myanimebot.utils as utils
import myanimebot.globals as globals

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


async def ping_cmd(message, channel):
	''' Responds to ping command '''
	messageTimestamp = message.created_at
	currentTimestamp = datetime.datetime.utcnow()
	delta = round((currentTimestamp - messageTimestamp).total_seconds() * 1000)
	
	await channel.send("pong (" + str(delta) + "ms)")


async def about_cmd(channel):
    ''' Responds to about command with a brief description of this bot '''

    title = "MyAnimeBot version {} by Penta & lulu".format(globals.VERSION)
    description = """MyAnimeBot checks MyAnimeList and Anilist profiles for specified users, and send a message for every new activities found.
        More help with the **{} help** command.
        
        Check our GitHub page for more informations: https://github.com/Penta/MyAnimeBot
        """.format(globals.prefix)

    await channel.send(embed=discord.Embed(colour=0x777777, title=title, description=description).set_thumbnail(url=globals.iconBot))


async def help_cmd(channel):
    ''' Responds to help command '''

    embed = discord.Embed(title="***MyAnimeBot Commands***", colour=0xEED000)
    embed.add_field(name="`here`", value="Register this channel. The bot will send new activities on registered channels.")
    embed.add_field(name="`stop`", value="Un-register this channel. The bot will now stop sending new activities for this channel.")
    embed.add_field(name="`info [mal|ani]`", value="Get the registered users for this server. Users can be filtered by specifying a service.")
    embed.add_field(name="`add {mal|ani} <user>`", value="Register a user for a specific service.\nEx: `add mal MyUser`")
    embed.add_field(name="`delete {mal|ani} <user>`", value="Remove a user for a specific service.\nEx: `delete ani MyUser`")
    embed.add_field(name="`role <@discord_role>`", value="Specify a role that is able to manage the bot.\nEx: `role @Moderator`, `role @everyone`")
    embed.add_field(name="`top`", value="Show statistics for this server.")
    embed.add_field(name="`ping`", value="Ping the bot.")
    embed.add_field(name="`about`", value="Get some information about this bot")
    await channel.send(embed=embed)
