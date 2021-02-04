import discord.ext.commands as discord_cmds

import myanimebot.utils as utils
import myanimebot.globals as globals
import myanimebot.commands.permissions as permissions
import myanimebot.commands.converters as converters


@discord_cmds.command(name="delete")
@discord_cmds.check(permissions.in_allowed_role)
async def delete_user_cmd(ctx, service : converters.to_service, user : str):
    ''' Processes the command "delete" and remove a registered user '''

    server = ctx.guild
    server_id = str(server.id)
    
    user_servers = utils.get_user_servers(user, service)
    # If user is not present in the database
    if user_servers is None:
        return await ctx.send("The user **" + user + "** is not in our database for this server!")

    # Else if present, update the servers for this user
    srv_string = utils.remove_server_from_servers(server_id, user_servers)
    
    if srv_string is None: # Server not present in the user's servers
        return await ctx.send("The user **" + user + "** is not in our database for this server!")

    if srv_string == "":
        utils.delete_user_from_db(user, service)
    else:
        utils.update_user_servers_db(user, service, srv_string)

    return await ctx.send("**{}** deleted from the database for this server.".format(user))


@delete_user_cmd.error
async def delete_user_cmd_error(ctx, error):
    ''' Processes errors from delete cmd '''

    if isinstance(error, discord_cmds.MissingRequiredArgument):
        return await ctx.send("Usage: {} add **{}**/**{}** **username**".format(globals.prefix, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
    elif isinstance(error, discord_cmds.ConversionError):
        return await ctx.send('Incorrect service {}. Use **"{}"** or **"{}"** for example'.format(error.original, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
