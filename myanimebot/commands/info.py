import discord.ext.commands as discord_cmds

from typing import List, Optional

import myanimebot.utils as utils
import myanimebot.globals as globals
import myanimebot.commands.converters as converters


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

    if filters is None: return []

    filters_list = []
    for filter in filters.split(','):
        try:
            filters_list.append(utils.Service.from_str(filter))
        except NotImplementedError:
            pass # Ignore incorrect filter
    return filters_list


@discord_cmds.command(name="info")
async def info_cmd(ctx, filters : Optional[get_service_filters_list]):
    ''' Processes the command "info" and sends a message '''

    server = ctx.guild
    if utils.is_server_in_db(server.id) == False:
         await ctx.send("The server **{}** is not in our database.".format(server))
    else:
        users = utils.get_users()
        channels = utils.get_channels(server.id)
        role = utils.get_allowed_role(server.id)
        if channels is None:
            await ctx.send("No channel assigned for this bot on this server.")
        else:
            await ctx.send(build_info_cmd_message(users, server, channels, utils.get_role_name(role, server), filters))


@info_cmd.error
async def info_cmd_error(ctx, error):
    ''' Processes errors from info cmd '''

    # Should not happen
    if isinstance(error, discord_cmds.ConversionError):
        globals.logger.error('[info_cmd] An error occured when trying to convert {} to List[Service] filters: {}'.format(error.original, error))

