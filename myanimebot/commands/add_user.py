import urllib
import discord.ext.commands as discord_cmds

from typing import Tuple

import myanimebot.utils as utils
import myanimebot.globals as globals
import myanimebot.anilist as anilist
import myanimebot.commands.permissions as permissions
import myanimebot.commands.converters as converters


def check_user_name_validity(user_name: str, service : utils.Service) -> Tuple[bool, str]:
    """ Check if user_name exists on a specific service.
        
        Returns:
            - bool: 	True if user_name exists
            - str:		Error string if the user does not exist
    """

    if(len(user_name) > globals.USERNAME_MAX_LENGTH):
        return False, "Username too long!"

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


@discord_cmds.command(name="add")
@discord_cmds.check(permissions.in_allowed_role)
async def add_user_cmd(ctx, service : converters.to_service, user : str):
    ''' Processes the command "add" and add a user to fetch the data for '''

    if user is None:
        return await ctx.send("Usage: {} add **{}**/**{}** **username**".format(globals.prefix, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
    elif service is None:
        return await ctx.send('Incorrect service. Use **"{}"** or **"{}"** for example'.format(globals.SERVICE_MAL, globals.SERVICE_ANILIST))

    server = ctx.guild
    server_id = str(server.id)

    try:
        # Check user validity
        is_valid, error_string = check_user_name_validity(user, service)
        if is_valid == False:
            return await ctx.send(error_string)

        # Get user's servers
        user_servers = utils.get_user_servers(user, service)
        # User not present in database
        if user_servers is None: 
            utils.insert_user_into_db(user, service, server_id)
            return await ctx.send("**{}** added to the database for the server **{}**.".format(user, server))
        else: # User present in database

            is_server_present = server_id in user_servers.split(',')
            if is_server_present == True: # The user already has registered this server
                return await ctx.send("User **{}** is already registered in our database for this server!".format(user))
            else:
                new_servers = '{},{}'.format(user_servers, server_id)
                utils.update_user_servers_db(user, service, new_servers)					
                return await ctx.send("**{}** added to the database for the server **{}**.".format(user, server))
    except Exception as e:
        globals.logger.warning("Error while adding user '{}' on server '{}': {}".format(user, server, str(e)))
        return await ctx.send("An unknown error occured while addind this user, the error has been logged.")


@add_user_cmd.error
async def add_user_cmd_error(ctx, error):
    ''' Processes errors from add cmd '''
    
    if isinstance(error, discord_cmds.MissingRequiredArgument):
        return await ctx.send("Usage: {} add **{}**/**{}** **username**".format(globals.prefix, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
    elif isinstance(error, discord_cmds.ConversionError):
        return await ctx.send('Incorrect service {}. Use **"{}"** or **"{}"** for example'.format(error.original, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
