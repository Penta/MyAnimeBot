import discord.ext.commands as discord_cmds


import myanimebot.globals as globals
import myanimebot.commands.permissions as permissions


@discord_cmds.command(name="role")
@discord_cmds.check(permissions.is_administrator)
async def role_cmd(ctx, role : str):
    ''' Processes the command "role" and registers a role to be able to use the bot's commands '''

    server = ctx.guild
    message = ctx.message
    

    if (role == "everyone") or (role == "@everyone"):
        cursor = globals.conn.cursor(buffered=True)
        cursor.execute("UPDATE t_servers SET admin_group = NULL WHERE server = %s", [str(server.id)])
        globals.conn.commit()
        cursor.close()

        await ctx.send("Everyone is now allowed to use the bot.")
    else: # A role is found
        rolesFound = message.role_mentions

        if (len(rolesFound) == 0):
            return await ctx.send("Please specify a correct role.")
        elif (len(rolesFound) > 1):
            return await ctx.send("Please specify only 1 role.")
        else:
            roleFound = rolesFound[0]
            # Update db with newly added role
            cursor = globals.conn.cursor(buffered=True)
            cursor.execute("UPDATE t_servers SET admin_group = %s WHERE server = %s", [str(roleFound.id), str(server.id)])
            globals.conn.commit()
            cursor.close()

            await ctx.send("The role **{}** is now allowed to use this bot!".format(roleFound.name))


@role_cmd.error
async def role_cmd_error(ctx, error):
    ''' Processes errors from role cmd '''

    if isinstance(error, discord_cmds.MissingRequiredArgument):
        return await ctx.send("Usage: {} add **{}**/**{}** **username**".format(globals.prefix, globals.SERVICE_MAL, globals.SERVICE_ANILIST))
