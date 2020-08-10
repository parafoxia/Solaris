# S4 - A security and statistics focussed Discord bot.
# Copyright (C) 2020  Ethan Henderson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Ethan Henderson
# parafoxia@carberra.xyz

import discord

from solaris.utils import string
from solaris.utils.modules import retrieve

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
    """The server prefix
    The prefix S4 responds to, aside from mentions. The default is >>."""
    if not isinstance(value, str):
        await channel.send(f"{bot.cross} The server prefix must be a string.")
    elif len(value) > MAX_PREFIX_LEN:
        await channel.send(f"{bot.cross} The server prefix must be no longer than 5 characters in length.")
    else:
        await bot.db.execute("UPDATE system SET Prefix = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(f"{bot.tick} The server prefix has been set to {value}.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The server prefix has been set to {value}.")


async def system__logchannel(bot, channel, value):
    """The log channel
    The channel S4 uses to communicate important information. It is recommended you keep this channel restricted to members of the server's moderation team. Upon selecting a new channel, S4 will delete the one that was created should it still exist."""
    if not isinstance(value, discord.TextChannel):
        await channel.send(f"{bot.cross} The log channel must be a Discord text channel in this server.")
    elif not value.permissions_for(channel.guild.me).send_messages:
        await channel.send(
            f"{bot.cross} The given channel can not be used as the log channel as S4 can not send messages to it."
        )
    else:
        await bot.db.execute("UPDATE system SET LogChannelID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(f"{bot.tick} The log channel has been set to {value.mention}.")
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
            await value.send(f"{bot.info} The default log channel has been deleted, as it is no longer required.")


async def system__adminrole(bot, channel, value):
    """The admin role
    The role used to denote which members can configure S4. Alongside server administrators, only members with this role can use any of S4's configuration commands. Upon selecting a new channel, S4 will delete the one that was created should it still exist."""
    if not isinstance(value, discord.Role):
        await channel.send(f"{bot.cross} The admin role must be a Discord role in this server.")
    elif value.position > channel.guild.me.top_role.position:
        await channel.send(
            f"{bot.cross} The given role can not be used as the admin role as it is above S4's top role in the role hierarchy."
        )
    else:
        await bot.db.execute("UPDATE system SET AdminRoleID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(f"{bot.tick} The admin role has been set to {value.mention}.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The admin role has been set to {value.mention}.")

        if (
            channel.guild.me.guild_permissions.manage_roles
            and (dar := await retrieve.system__defaultadminrole(bot, channel.guild)) is not None
        ):
            await dar.delete(reason="Default admin role was overridden.")
            lc = await retrieve.log_channel(bot, channel.guild)
            await lc.send(f"{bot.info} The default admin role has been deleted, as it is no longer required.")


async def _gateway__active(bot, channel, value):
    await bot.db.execute("UPDATE gateway SET Active = ? WHERE GuildID = ?", value, channel.guild.id)


async def gateway__ruleschannel(bot, channel, value):
    """The rules channel
    The channel that the gate message will be sent to when the module is activated. This channel should contain the server rules, and should be the first channel new members see when they enter the server."""
    if await retrieve._gateway__active(bot, channel.guild):
        await channel.send(f"{bot.cross} This can not be done as the gateway module is currently active.")
    elif not isinstance(value, discord.TextChannel):
        await channel.send(f"{bot.cross} The rules channel must be a Discord text channel in this server.")
    elif not (
        value.permissions_for(channel.guild.me).send_messages
        and value.permissions_for(channel.guild.me).manage_messages
    ):
        await channel.send(
            f"{bot.cross} The given channel can not be used as the rules channel as S4 can not send messages to it or manage exising messages there."
        )
    else:
        await bot.db.execute("UPDATE gateway SET RulesChannelID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(
            f"{bot.tick} The rules channel has been set to {value.mention}. Make sure this is the first channel new members see when they join."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The rules channel has been set to {value.mention}.")


async def _gateway__gatemessage(bot, channel, value):
    if value is not None:
        await bot.db.execute("UPDATE gateway SET GateMessageID = ? WHERE GuildID = ?", value.id, channel.guild.id)
    else:
        await bot.db.execute("UPDATE gateway SET GateMessageID = NULL WHERE GuildID = ?", channel.guild.id)


async def gateway__blockingrole(bot, channel, value):
    """The blockng role
    The role that S4 will give new members upon entering the server, and remove when they accept the server rules. This role should prohibit access to all but the rules channel, or all but a read-only category."""
    if await retrieve._gateway__active(bot, channel.guild):
        await channel.send(f"{bot.cross} This can not be done as the gateway module is currently active.")
    elif not isinstance(value, discord.Role):
        await channel.send(f"{bot.cross} The blocking role must be a Discord role in this server.")
    elif value.position >= channel.guild.me.top_role.position:
        await channel.send(
            f"{bot.cross} The given role can not be used as the blocking role as it is above S4's top role in the role hierarchy."
        )
    else:
        await bot.db.execute("UPDATE gateway SET BlockingRoleID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(
            f"{bot.tick} The blocking role has been set to {value.mention}. Make sure the permissions are set correctly."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The blocking role has been set to {value.mention}.")


async def gateway__memberroles(bot, channel, values):
    """The member roles
    The role(s) that S4 will give members upon accepting the server rules. This is optional, but could be useful if you want members to have specific role when they join, for example for a levelling system, or automatically opt them in to server announcements. You can set up to 3 member roles. The roles can be unset any time by passing no arguments to the command below."""
    values = [values] if not isinstance(values, list) else values

    if (br := await retrieve.gateway__blockingrole(bot, channel.guild)) is None:
        await channel.send(f"{bot.cross} You need to set the blocking role before you can set the member roles.")
    elif values[0] is None:
        await bot.db.execute("UPDATE gateway SET MemberRoleIDs = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The member roles have been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The member roles have been reset.")
    elif len(values) > MAX_MEMBER_ROLES:
        await channel.send(f"{bot.cross} You can only set up to {MAX_MEMBER_ROLES} member roles.")
    elif not all(isinstance(v, discord.Role) for v in values):
        await channel.send(f"{bot.cross} All member roles must be Discord roles in this server.")
    elif any(v == br for v in values):
        await channel.send(f"{bot.cross} No member roles can be the same as the blocking role.")
    elif any(v.position > channel.guild.me.top_role.position for v in values):
        await channel.send(
            f"{bot.cross} One or more given roles can not be used as member roles as they are above S4's top role in the role hierarchy."
        )
    else:
        await bot.db.execute(
            "UPDATE gateway SET MemberRoleIDs = ? WHERE GuildID = ?",
            ",".join(f"{v.id}" for v in values),
            channel.guild.id,
        )
        await channel.send(
            f"{bot.tick} The member roles have been set to {string.list_of([v.mention for v in values])}. Make sure the permissions are set correctly."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The member roles have been set to {string.list_of([v.mention for v in values])}.")


async def gateway__exceptionroles(bot, channel, values):
    """The exception roles
    The role(s) that, when given to a new member before they accept the server rules, will grant them access to the server. This is optional, but could be useful if you want members to have access upon receiving a premium role, for example, one given by the Patreon bot. You can set up to 3 member roles. The roles can be unset any time by passing no arguments to the command below."""
    values = [values] if not isinstance(values, list) else values

    if (br := await retrieve.gateway__blockingrole(bot, channel.guild)) is None:
        await channel.send(f"{bot.cross} You need to set the blocking role before you can set the exception roles.")
    elif values[0] is None:
        await bot.db.execute("UPDATE gateway SET ExceptionRoleIDs = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The exception roles have been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The exception roles have been reset.")
    elif len(values) > MAX_EXCEPTION_ROLES:
        await channel.send(f"{bot.cross} You can only set up to {MAX_EXCEPTION_ROLES} exception roles.")
    elif not all(isinstance(v, discord.Role) for v in values):
        await channel.send(f"{bot.cross} All exception roles must be Discord roles in this server.")
    elif any(v == br for v in values):
        await channel.send(f"{bot.cross} No exception roles can be the same as the blocking role.")
    else:
        await bot.db.execute(
            "UPDATE gateway SET ExceptionRoleIDs = ? WHERE GuildID = ?",
            ",".join(f"{v.id}" for v in values),
            channel.guild.id,
        )
        await channel.send(
            f"{bot.tick} The exception roles have been set to {string.list_of([v.mention for v in values])}."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(
            f"{bot.info} The exception roles have been set to {string.list_of([v.mention for v in values])}."
        )


async def gateway__welcomechannel(bot, channel, value):
    """The welcome channel
    The channel that S4 will send welcome messages to upon a member accepting the server rules. If no channel is set, S4 will not send welcome messages. The channel can be unset any time by passing no arguments to the command below. Note that S4 does not send welcome messages in all situations, such as if the member received an exception role."""
    if (rc := await retrieve.gateway__ruleschannel(bot, channel.guild)) is None:
        await channel.send(f"{bot.cross} You need to set the rules channel before you can set the welcome channel.")
    elif value is None:
        await bot.db.execute("UPDATE gateway SET WelcomeChannelID = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The welcome channel has been reset. S4 will stop sending welcome messages.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The welcome channel has been reset.")
    elif not isinstance(value, discord.TextChannel):
        await channel.send(f"{bot.cross} The welcome channel must be a Discord text channel in this server.")
    elif value == rc:
        await channel.send(f"{bot.cross} The welcome channel can not be the same as the rules channel.")
    elif not value.permissions_for(channel.guild.me).send_messages:
        await channel.send(
            f"{bot.cross} The given channel can not be used as the welcome channel as S4 can not send messages to it."
        )
    else:
        await bot.db.execute("UPDATE gateway SET WelcomeChannelID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(f"{bot.tick} The welcome channel has been set to {value.mention}.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The welcome channel has been set to {value.mention}.")


async def gateway__goodbyechannel(bot, channel, value):
    """The goodbye channel
    The channel that S4 will send goodbye messages to upon a member leaving the server. If no channel is set, S4 will not send goodbye messages. The channel can be unset any time by passing no arguments to the command below. Note that S4 will only send goodbye messages for members who have accepted the server rules, or members who were in the server before the module was activated."""
    if (rc := await retrieve.gateway__ruleschannel(bot, channel.guild)) is None:
        await channel.send(f"{bot.cross} You need to set the rules channel before you can set the goodbye channel.")
    elif value is None:
        await bot.db.execute("UPDATE gateway SET GoodbyeChannelID = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The goodbye channel has been reset. S4 will stop sending goodbye messages.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The goodbye channel has been reset.")
    elif not isinstance(value, discord.TextChannel):
        await channel.send(f"{bot.cross} The goodbye channel must be a Discord text channel in this server.")
    elif value == rc:
        await channel.send(f"{bot.cross} The goodbye channel can not be the same as the rules channel.")
    elif not value.permissions_for(channel.guild.me).send_messages:
        await channel.send(
            f"{bot.cross} The given channel can not be used as the goodbye channel as S4 can not send messages to it."
        )
    else:
        await bot.db.execute("UPDATE gateway SET GoodbyeChannelID = ? WHERE GuildID = ?", value.id, channel.guild.id)
        await channel.send(f"{bot.tick} The goodbye channel has been set to {value.mention}.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The goodbye channel has been set to {value.mention}.")


async def gateway__timeout(bot, channel, value):
    """The gateway timeout
    The amount of time S4 gives new members to react to the gate message before being kicked. This is set in minutes, and can be set to any value between 1 and 60 inclusive. If no timeout is set, the default is 5 minutes. This can be reset any time by passing no arguments to the command below."""
    if value is None:
        await bot.db.execute("UPDATE gateway SET Timeout = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The timeout has been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The timeout has been reset.")
    elif not isinstance(value, int):
        await channel.send(f"{bot.cross} The timeout must be an integer number.")
    elif not MIN_TIMEOUT <= value <= MAX_TIMEOUT:
        await channel.send(f"{bot.cross} The timeout must be between 1 and 60 minutes inclusive.")
    else:
        await bot.db.execute("UPDATE gateway SET Timeout = ? WHERE GuildID = ?", value * 60, channel.guild.id)
        await channel.send(
            f"{bot.tick} The timeout has been set to {value} minute(s). This will only apply to members who enter the server from now."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The timeout has been set to {value} minute(s).")


async def gateway__gatetext(bot, channel, value):
    """The gate message text
    The message displayed in the gate message. This is probably the first thing members will see when joining the server, so make sure it is set correctly. The message can be up to 250 characters in length, and should **not** contain the server rules. If no message is set, a default will be used instead. The message can be reset any time by passing no arguments to the command below."""
    if value is None:
        await bot.db.execute("UPDATE gateway SET GateText = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(
            f"{bot.tick} The gate message text has been reset. The module needs to be restarted for these changes to take effect."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The gate message text has been reset.")
    elif not isinstance(value, str):
        await channel.send(f"{bot.cross} The gate message text must be a string.")
    elif len(value) > MAX_GATETEXT_LEN:
        await channel.send(
            f"{bot.cross} The gate message text must be no longer than {MAX_GATETEXT_LEN:,} characters in length."
        )
    elif not string.text_is_formattible(value):
        await channel.send(f"{bot.cross} The given message is not formattible (probably unclosed brace).")
    else:
        await bot.db.execute("UPDATE gateway SET GateText = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(
            f"{bot.tick} The gate message text has been set. The module needs to be restarted for these changes to take effect."
        )
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The gate message text has been set to the following: {value}")


async def gateway__welcometext(bot, channel, value):
    """The welcome message text
    The message sent to the welcome channel (if set) when a new member accepts the server rules. This message can be up to 1,000 characters in length. If no message is set, a default will be used instead. The message can be reset any time by passing no arguments to the command below."""
    if value is None:
        await bot.db.execute("UPDATE gateway SET WelcomeText = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The welcome message text has been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The welcome message text has been reset.")
    elif not isinstance(value, str):
        await channel.send(f"{bot.cross} The welcome message text must be a string.")
    elif len(value) > MAX_WGTEXT_LEN:
        await channel.send(
            f"{bot.cross} The welcome message text must be no longer than {MAX_WGTEXT_LEN:,} characters in length."
        )
    elif not string.text_is_formattible(value):
        await channel.send(f"{bot.cross} The given message is not formattible (probably unclosed brace).")
    else:
        await bot.db.execute("UPDATE gateway SET WelcomeText = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(f"{bot.tick} The welcome message text has been set.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The welcome message text has been set to the following: {value}")


async def gateway__goodbyetext(bot, channel, value):
    """The goodbye message text
    The message sent to the goodbye channel (if set) when a member leaves the server. This message can be up to 1,000 characters in length. If no message is set, a default will be used instead. The message can be reset any time by passing no arguments to the command below."""
    if value is None:
        await bot.db.execute("UPDATE gateway SET GoodbyeText = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The goodbye message text has been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The goodbye message text has been reset.")
    elif not isinstance(value, str):
        await channel.send(f"{bot.cross} The goodbye message text must be a string.")
    elif len(value) > MAX_WGTEXT_LEN:
        await channel.send(
            f"{bot.cross} The goodbye message text must be no longer than {MAX_WGTEXT_LEN:,} characters in length."
        )
    elif not string.text_is_formattible(value):
        await channel.send(f"{bot.cross} The given message is not formattible (probably unclosed brace).")
    else:
        await bot.db.execute("UPDATE gateway SET GoodbyeText = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(f"{bot.tick} The goodbye message text has been set.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The goodbye message text has been set to the following: {value}")


async def gateway__welcomebottext(bot, channel, value):
    """The welcome message text for bots
    The message sent to the welcome channel (if set) when a bot joins the server. This message can be up to 500 characters in length. If no message is set, a default will be used instead. The message can be reset any time by passing no arguments to the command below."""
    if value is None:
        await bot.db.execute("UPDATE gateway SET WelcomeBotText = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The welcome bot message text has been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The welcome bot message text has been reset.")
    elif not isinstance(value, str):
        await channel.send(f"{bot.cross} The welcome bot message text must be a string.")
    elif len(value) > MAX_WGBOTTEXT_LEN:
        await channel.send(
            f"{bot.cross} The welcome bot message text must be no longer than {MAX_WGBOTTEXT_LEN:,} characters in length."
        )
    elif not string.text_is_formattible(value):
        await channel.send(f"{bot.cross} The given message is not formattible (probably unclosed brace).")
    else:
        await bot.db.execute("UPDATE gateway SET WelcomeBotText = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(f"{bot.tick} The welcome bot message text has been set.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The welcome bot message text has been set to the following: {value}")


async def gateway__goodbyebottext(bot, channel, value):
    """The goodbye message text for bots
    The message sent to the welcome channel (if set) when a bot leaves the server. This message can be up to 500 characters in length. If no message is set, a default will be used instead. The message can be reset any time by passing no arguments to the command below."""
    if value is None:
        await bot.db.execute("UPDATE gateway SET GoodbyeBotText = NULL WHERE GuildID = ?", channel.guild.id)
        await channel.send(f"{bot.tick} The goodbye bot message text has been reset.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The goodbye bot message text has been reset.")
    elif not isinstance(value, str):
        await channel.send(f"{bot.cross} The goodbye bot message text must be a string.")
    elif len(value) > MAX_WGBOTTEXT_LEN:
        await channel.send(
            f"{bot.cross} The goodbye bot message text must be no longer than {MAX_WGBOTTEXT_LEN:,} characters in length."
        )
    elif not string.text_is_formattible(value):
        await channel.send(f"{bot.cross} The given message is not formattible (probably unclosed brace).")
    else:
        await bot.db.execute("UPDATE gateway SET GoodbyeBotText = ? WHERE GuildID = ?", value, channel.guild.id)
        await channel.send(f"{bot.tick} The goodbye bot message text has been set.")
        lc = await retrieve.log_channel(bot, channel.guild)
        await lc.send(f"{bot.info} The goodbye bot message text has been set to the following: {value}")
