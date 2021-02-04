import discord.ext.commands as discord_cmds


import myanimebot.utils as utils
import myanimebot.globals as globals
import myanimebot.commands.permissions as permissions


@discord_cmds.command(name="stop")
@discord_cmds.check(permissions.in_allowed_role)
async def stop_cmd(ctx):
    ''' Processes the command "stop" and unregisters a channel '''

    server = ctx.guild

    if utils.is_server_in_db(server.id):
        # Remove server from DB
        cursor = globals.conn.cursor(buffered=True)
        cursor.execute("DELETE FROM t_servers WHERE server = {}".format(server.id))
        globals.conn.commit()

        await ctx.send("Server **{}** is now unregistered from our database.".format(server))
    else:
        await ctx.send("Server **{}** was already not registered.".format(server))
