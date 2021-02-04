import discord
import myanimebot.utils as utils
import myanimebot.globals as globals


async def in_allowed_role(ctx) -> bool :
    ''' Checks if a user has the permissions to configure the bot on a specific server '''

    user = ctx.author
    server = ctx.guild

    targetRole = utils.get_allowed_role(server.id)
    globals.logger.debug ("Role target: " + str(targetRole))

    if user.guild_permissions.administrator:
        globals.logger.debug (str(user) + " is server admin on " + str(server) + "!")
        return True
    elif (targetRole is None):
        globals.logger.debug ("No role specified for " + str(server))
        return True
    else:
        for role in user.roles:
            if str(role.id) == str(targetRole):
                globals.logger.debug ("Permissions validated for " + str(user))
                return True

    await ctx.send("Only allowed users can use this command!")
    return False


async def is_administrator(ctx) -> bool :
    ''' Checks if a user is a server's adminitrator '''

    if ctx.author.guild_permissions.administrator:
        return True
    
    await ctx.send("Only server's admins can use this command.")
    return False
