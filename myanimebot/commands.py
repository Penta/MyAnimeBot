import discord
import urllib
import datetime

from typing import List, Tuple

import myanimebot.utils as utils
import myanimebot.globals as globals
import myanimebot.anilist as anilist
import myanimebot.database as database

def build_info_cmd_message(users, server, channels, role, filters : List[utils.Service]) -> str:
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
        if role is not None:
            message += '\nAllowed role: **{}**'.format(role)
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


def in_allowed_role(user : discord.Member, server : int) -> bool :
    ''' Check if a user has the permissions to configure the bot on a specific server '''

    targetRole = utils.get_allowed_role(server.id)
    globals.logger.debug ("Role target: " + str(targetRole))

    if user.guild_permissions.administrator:
        globals.logger.debug (str(user) + " is server admin on " + str(server) + "!")
        return True
    elif (targetRole is None):
        globals.logger.debug ("No group specified for " + str(server))
        return True
    else:
        for role in user.roles:
            if str(role.id) == str(targetRole):
                globals.logger.debug ("Permissions validated for " + str(user))
                return True

    return False


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

    # Verify that the user is allowed
    if in_allowed_role(message.author, message.guild) is False:
        return await message.channel.send("Only allowed users can use this command!")

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

    # Verify that the user is allowed
    if in_allowed_role(message.author, message.guild) is False:
        return await message.channel.send("Only allowed users can use this command!")

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
        role = utils.get_allowed_role(server.id)
        if channels is None:
            await message.channel.send("No channel assigned for this bot on this server.")
        else:
            await message.channel.send(build_info_cmd_message(users, server, channels, utils.get_role_name(role, server), filters))


async def ping_cmd(message, channel):
    ''' Responds to ping command '''
    messageTimestamp = message.created_at
    currentTimestamp = datetime.datetime.utcnow()
    delta = round((currentTimestamp - messageTimestamp).total_seconds() * 1000)

    await message.reply("pong ({}ms)".format(delta))


async def about_cmd(channel):
    ''' Responds to about command with a brief description of this bot '''

    embed = discord.Embed(title="***MyAnimeBot Commands***", colour=0xEED000)
    embed.title = "MyAnimeBot version {} by Penta & lulu".format(globals.VERSION)
    embed.colour = 0xEED000
    embed.description = """MyAnimeBot checks MyAnimeList and Anilist profiles for specified users, and send a message for every new activities found.
        More help with the **{} help** command.
        
        Check our GitHub page for more informations: https://github.com/Penta/MyAnimeBot
        """.format(globals.prefix)
    embed.set_thumbnail(url=globals.iconBot)

    await channel.send(embed=embed)


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


async def here_cmd(author, server, channel):
    ''' Processes the command "here" and registers a channel to send new found feeds '''

    # Verify that the user is allowed
    if in_allowed_role(author, server) is False:
        return await channel.send("Only allowed users can use this command!")
    
    if utils.is_server_in_db(server.id):
        # Server in DB, so we need to update the channel

        # Check if channel already registered
        channels = utils.get_channels(server.id)
        channels_id = [channel["channel"] for channel in channels]
        globals.logger.debug("Channels {} and channel id {}".format(channels_id, channel.id))
        if (str(channel.id) in channels_id):
            await channel.send("Channel **{}** already in use for this server.".format(channel))
        else:
            cursor = database.create_cursor()
            cursor.execute("UPDATE t_servers SET channel = {} WHERE server = '{}'".format(channel.id, server.id))
            globals.conn.commit()
            
            await channel.send("Channel updated to: **{}**.".format(channel))
            
        cursor.close()
    else:
        # No server found in DB, so register it
        cursor = database.create_cursor()
        cursor.execute("INSERT INTO t_servers (server, channel) VALUES ('{}',{})".format(server.id, channel.id))
        globals.conn.commit() # TODO Move to corresponding file
        
        await channel.send("Channel **{}** configured for **{}**.".format(channel, server))


async def stop_cmd(author, server, channel):
    ''' Processes the command "stop" and unregisters a channel '''

    # Verify that the user is allowed
    if in_allowed_role(author, server) is False:
        return await channel.send("Only allowed users can use this command!")

    if utils.is_server_in_db(server.id):
        # Remove server from DB
        cursor = database.create_cursor()
        cursor.execute("DELETE FROM t_servers WHERE server = {}".format(server.id))
        globals.conn.commit()

        await channel.send("Server **{}** is now unregistered from our database.".format(server))
    else:
        await channel.send("Server **{}** was already not registered.".format(server))


async def role_cmd(words, message, author, server, channel):
    ''' Processes the command "role" and registers a role to be able to use the bot's commands '''

    if len(words) <= 2:
        return await channel.send("A role must be specified.")

    if not author.guild_permissions.administrator:
        return await channel.send("Only server's admins can use this command.")


    role_str = words[2]
    if (role_str == "everyone") or (role_str == "@everyone"):
        cursor = database.create_cursor()
        cursor.execute("UPDATE t_servers SET admin_group = NULL WHERE server = %s", [str(server.id)])
        globals.conn.commit()
        cursor.close()

        await channel.send("Everyone is now allowed to use the bot.")
    else: # A role is found
        rolesFound = message.role_mentions

        if (len(rolesFound) == 0):
            return await channel.send("Please specify a correct role.")
        elif (len(rolesFound) > 1):
            return await channel.send("Please specify only 1 role.")
        else:
            roleFound = rolesFound[0]
            # Update db with newly added role
            cursor = database.create_cursor()
            cursor.execute("UPDATE t_servers SET admin_group = %s WHERE server = %s", [str(roleFound.id), str(server.id)])
            globals.conn.commit()
            cursor.close()

            await channel.send("The role **{}** is now allowed to use this bot!".format(roleFound.name))


async def top_cmd(words, channel):
    ''' Processes the command "top" and returns statistics on registered feeds '''

    # TODO Redo this function

    if len(words) == 2:
        try:
            cursor = database.create_cursor()
            cursor.execute("SELECT * FROM v_Top")
            data = cursor.fetchone()
            
            if data is None: await message.channel.send("It seems that there is no statistics... (what happened?!)")
            else:
                topText = "**__Here is the global statistics of this bot:__**\n\n"
                
                while data is not None:
                    topText += " - " + str(data[0]) + ": " + str(data[1]) + "\n"
                        
                    data = cursor.fetchone()
                    
                cursor = database.create_cursor()
                cursor.execute("SELECT * FROM v_TotalFeeds")
                data = cursor.fetchone()
                
                topText += "\n***Total user entry***: " + str(data[0])
                
                cursor = database.create_cursor()
                cursor.execute("SELECT * FROM v_TotalAnimes")
                data = cursor.fetchone()
                
                topText += "\n***Total unique manga/anime***: " + str(data[0])
                
                await channel.send(topText)
            
            cursor.close()
        except Exception as e:
            globals.logger.warning("An error occured while displaying the global top: " + str(e))
            await channel.send("Unable to reply to your request at the moment...")
    elif len(words) > 2:
        keyword = str(' '.join(words[2:]))
        globals.logger.info("Displaying the global top for the keyword: " + keyword)
        
        try:
            cursor = database.create_cursor()
            cursor.callproc('sp_UsersPerKeyword', [str(keyword), 20])
            result = cursor.fetchall();
            topKeyText = ""

            for data in result:
                    topKeyText += " - {}: {}\n".format(data[0], data[1])

            if (topKeyText != ""):
                await channel.send("**__Here is the statistics for the keyword {}:__**\n\n{}".format(keyword, topKeyText))
            else:
                await channel.send("It seems that there is no statistics for the keyword **{}**.".format(keyword))

            cursor.close()
        except Exception as e:
            globals.logger.warning("An error occured while displaying the global top for keyword '" + keyword + "': " + str(e))
            await channel.send("Unable to reply to your request at the moment...")


async def on_mention(channel):
    return await channel.send(":heart:")