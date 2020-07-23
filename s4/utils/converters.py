import discord
from discord.ext import commands

from s4.utils import Search


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
