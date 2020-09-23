# Solaris - A Discord bot designed to make your server a safer and better place.
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

from discord.ext import commands

from solaris.utils import modules


class CustomCheckFailure(commands.CheckFailure):
    def __init__(self, message):
        self.msg = message


class BotHasNotBooted(CustomCheckFailure):
    def __init__(self):
        super().__init__("Solaris is still booting. Please try again later.")


def bot_has_booted():
    async def predicate(ctx):
        if not ctx.bot.ready.booted:
            raise BotHasNotBooted()
        return True

    return commands.check(predicate)


class ModuleHasNotInitialised(CustomCheckFailure):
    def __init__(self, module):
        super().__init__(f"The {module} module is still initialising. Please try again later.")


def module_has_initialised(module):
    async def predicate(ctx):
        if not getattr(ctx.bot.ready, module):
            raise ModuleHasNotInitialised(module)
        return True

    return commands.check(predicate)


class BotIsNotReady(CustomCheckFailure):
    def __init__(self):
        super().__init__("Solaris is still performing some start-up procedures. Please try again later.")


def bot_is_ready():
    async def predicate(ctx):
        if not ctx.bot.ready.ok:
            raise BotIsNotReady()
        return True

    return commands.check(predicate)


class FirstTimeSetupNotRun(CustomCheckFailure):
    def __init__(self, prefix=">>", /):
        super().__init__(
            f"The first time setup needs to be run before you can do that. Use `{prefix}setup` to do this."
        )


def first_time_setup_has_run():
    async def predicate(ctx):
        if not await modules.retrieve._system__runfts(ctx.bot, ctx.guild):
            raise FirstTimeSetupNotRun(await ctx.bot.prefix(ctx.guild))
        return True

    return commands.check(predicate)


class FirstTimeSetupRun(CustomCheckFailure):
    def __init__(self):
        super().__init__("The first time setup has already been run.")


def first_time_setup_has_not_run():
    async def predicate(ctx):
        if await modules.retrieve._system__runfts(ctx.bot, ctx.guild):
            raise FirstTimeSetupRun()
        return True

    return commands.check(predicate)


class LogChannelNotSet(CustomCheckFailure):
    def __init__(self):
        super().__init__("The log channel has not been set.")


def log_channel_is_set():
    async def predicate(ctx):
        if not await modules.retrieve.system__logchannel(ctx.bot, ctx.guild):
            raise LogChannelNotSet()
        return True

    return commands.check(predicate)


class AdminRoleNotSet(CustomCheckFailure):
    def __init__(self):
        super().__init__("The admin role has not been set.")


def admin_role_is_set():
    async def predicate(ctx):
        if not await modules.retrieve.system__adminrole(ctx.bot, ctx.guild):
            raise AdminRoleNotSet()
        return True

    return commands.check(predicate)


class AuthorCanNotConfigure(CustomCheckFailure):
    def __init__(self):
        super().__init__("You are not able to configure Solaris.")


def author_can_configure():
    async def predicate(ctx):
        if not (
            ctx.author.guild_permissions.administrator
            or await modules.retrieve.system__adminrole(ctx.bot, ctx.guild) in ctx.author.roles
        ):
            raise AuthorCanNotConfigure()
        return True

    return commands.check(predicate)


class AuthorCanNotWarn(CustomCheckFailure):
    def __init__(self):
        super().__init__("You are not able to warn other members.")


def author_can_warn():
    async def predicate(ctx):
        if not (
            ctx.author.guild_permissions.administrator
            or await modules.retrieve.warn__warnrole(ctx.bot, ctx.guild) in ctx.author.roles
        ):
            raise AuthorCanNotWarn()
        return True

    return commands.check(predicate)


class ModuleIsNotActive(CustomCheckFailure):
    def __init__(self, module):
        super().__init__(f"The {module} module is not active.")


def module_is_active(module):
    async def predicate(ctx):
        if not await getattr(modules.retrieve, f"_{module}__active")(ctx.bot, ctx.guild):
            raise ModuleIsNotActive(module)
        return True

    return commands.check(predicate)


class ModuleIsActive(CustomCheckFailure):
    def __init__(self, module):
        super().__init__(f"The {module} module is already active.")


def module_is_not_active(module):
    async def predicate(ctx):
        if await getattr(modules.retrieve, f"_{module}__active")(ctx.bot, ctx.guild):
            raise ModuleIsActive(module)
        return True

    return commands.check(predicate)


class GuildIsDiscordBotList(CustomCheckFailure):
    def __init__(self):
        super().__init__(
            "In order to prevent unintended disruption, this command can not be run in the Discord Bot List server. If you wish to test module functionality, you will need to do so in another server."
        )


def guild_is_not_discord_bot_list():
    async def predicate(ctx):
        if ctx.guild.id == 264445053596991498:
            raise GuildIsDiscordBotList()
        return True

    return commands.check(predicate)
