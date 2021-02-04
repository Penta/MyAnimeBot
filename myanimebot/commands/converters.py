import discord.ext.commands as discord_cmds

import myanimebot.utils as utils

def to_service(service : str) -> utils.Service:
    try:
        return utils.Service.from_str(service)
    except NotImplementedError:
        raise discord_cmds.ConversionError(to_service, service)