import discord

from s4.utils.modules import retrieve

MAX_PREFIX_LEN = 5
MAX_MEMBER_ROLES = 3
MAX_EXCEPTION_ROLES = 3
MIN_TIMEOUT = 1
MAX_TIMEOUT = 60
MAX_GATETEXT_LEN = 250
MAX_WGTEXT_LEN = 1000
MAX_WGBOTTEXT_LEN = 500


async def _system__runfts(bot, channel, value):
    await bot.db.execute("UPDATE system SET RunFTS = ? WHERE GuildID = ?", value, channel.guild.id)


async def system__prefix(bot, channel, value):
    if not isinstance(value, str):
        await channel.send(f"{bot.cross} The server prefix must be a string.")
    elif len(value) > MAX_PREFIX_LEN:
        await channel.send(f"{bot.cross} The server prefix must be no longer than 5 characters in length.")
    else:
        await bot.db.execute("UPDATE system SET Prefix = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(f"{bot.tick} The server prefix was set to {value}.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The server prefix was set to {value}.")


async def system__logchannel(bot, channel, value):
    if not isinstance(value, discord.TextChannel):
        await channel.send(f"{bot.cross} The log channel must be a Discord text channel.")
    elif not value.permissions_for(channel.guild.me).send_messages:
        await channel.send(f"{bot.cross} That channel can not be used as S4 can not send messages to it.")
    else:
        await bot.db.execute("UPDATE system SET LogChannelID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(f"{bot.tick} The log channel was set to {value.mention}.")
        await value.send(
            (
                f"{bot.info} This is the new log channel. S4 will use this channel to communicate with you if needed. "
                "Configuration updates will also be sent here."
            )
        )

        if (
            channel.guild.me.guild_permissions.manage_channels
            and (dlc := await retrieve.system__defaultlogchannel(bot, channel.guild)) is not None
        ):
            await dlc.delete(reason="Default log channel was overridden.")
            await value.send(f"{bot.info} The default log channel was deleted, as it is no longer required.")


async def system__adminrole(bot, channel, value):
    if not isinstance(value, discord.Role):
        await channel.send(f"{bot.cross} The admin role must be a Discord role.")
    elif value.position > channel.guild.me.top_role.position:
        await channel.send(f"{bot.cross} The role can not be used as it is above S4's top role in the role hierarchy.")
    else:
        await bot.db.execute("UPDATE system SET AdminRoleID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(f"{bot.tick} The admin role was set to {value.mention}.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The admin role was set to {value.mention}.")

        if (
            channel.guild.me.guild_permissions.manage_roles
            and (dar := await retrieve.system__defaultadminrole(bot, channel.guild)) is not None
        ):
            await dar.delete(reason="Default admin role was overridden.")
            lc = await retrieve.log_channel(bot, channel.guild)
            await lc.send(f"{bot.info} The default admin role was deleted, as it is no longer required.")
