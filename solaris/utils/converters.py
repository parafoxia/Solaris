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

import discord
from discord.ext import commands

from solaris.utils import Search


class User(commands.Converter):
    async def convert(self, ctx, arg):
        return await ctx.bot.grab_user(arg)


class Channel(commands.Converter):
    async def convert(self, ctx, arg):
        return await ctx.bot.grab_channel(arg)


class Guild(commands.Converter):
    async def convert(self, ctx, arg):
        return await ctx.bot.grab_guild(arg)


class Command(commands.Converter):
    async def convert(self, ctx, arg):
        # False indicates command doesn't exist.
        return ctx.bot.get_command(arg) or False


class SearchedMember(commands.Converter):
    async def convert(self, ctx, arg):
        return discord.utils.get(
            ctx.guild.members,
            name=str(Search(arg, [m.display_name for m in ctx.guild.members]).best(min_accuracy=0.75)),
        )
