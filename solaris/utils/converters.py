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

import re

import discord
from discord.ext import commands

from solaris.utils import Search


class User(commands.Converter):
    async def convert(self, ctx, arg):
        if (user := await ctx.bot.grab_user(arg)) is None:
            raise commands.BadArgument
        return user


class Channel(commands.Converter):
    async def convert(self, ctx, arg):
        if (channel := await ctx.bot.grab_channel(arg)) is None:
            raise commands.BadArgument
        return channel


class Guild(commands.Converter):
    async def convert(self, ctx, arg):
        if (guild := await ctx.bot.grab_guild(arg)) is None:
            raise commands.BadArgument
        return guild


class Command(commands.Converter):
    async def convert(self, ctx, arg):
        if (c := ctx.bot.get_command(arg)) is not None:
            return c
        else:
            # Check for subcommands.
            for cmd in ctx.bot.walk_commands():
                if arg == f"{cmd.parent.name} {cmd.name}":
                    return cmd
        raise commands.BadArgument


class SearchedMember(commands.Converter):
    async def convert(self, ctx, arg):
        if (
            member := discord.utils.get(
                ctx.guild.members,
                name=str(Search(arg, [m.display_name for m in ctx.guild.members]).best(min_accuracy=0.75)),
            )
        ) is None:
            raise commands.BadArgument
        return member


class BannedUser(commands.Converter):
    async def convert(self, ctx, arg):
        if ctx.guild.me.guild_permissions.ban_members:
            if arg.isdigit():
                try:
                    return (await ctx.guild.fetch_ban(discord.Object(id=int(arg)))).user
                except discord.NotFound:
                    raise commands.BadArgument

            banned = [e.user for e in await ctx.guild.bans()]
            if banned:
                if (user := discord.utils.find(lambda u: str(u) == arg, banned)) is not None:
                    return user
                else:
                    raise commands.BadArgument
