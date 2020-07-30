async def _system__runfts(bot, guild):
    return await bot.db.field("SELECT RunFTS FROM system WHERE GuildID = ?", guild.id)


async def system__prefix(bot, guild):
    return await bot.db.field("SELECT Prefix FROM system WHERE GuildID = ?", guild.id)


async def system__defaultlogchannel(bot, guild):
    return bot.get_channel(await bot.db.field("SELECT DefaultLogChannelID FROM system WHERE GuildID = ?", guild.id))


async def system__logchannel(bot, guild):
    return bot.get_channel(await bot.db.field("SELECT LogChannelID FROM system WHERE GuildID = ?", guild.id))


async def log_channel(bot, guild):
    # An alias function.
    return await system__logchannel(bot, guild)


async def system__defaultadminrole(bot, guild):
    return guild.get_role(await bot.db.field("SELECT DefaultAdminRoleID FROM system WHERE GuildID = ?", guild.id))


async def system__adminrole(bot, guild):
    return guild.get_role(await bot.db.field("SELECT AdminRoleID FROM system WHERE GuildID = ?", guild.id))
