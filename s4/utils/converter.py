from discord.ext.commands import Converter

from s4.utils import Search


class FetchedUser(Converter):
    async def convert(self, ctx, arg):
        return await ctx.bot.fetch_user(arg)


class SearchedMember(Converter):
    async def convert(self, ctx, arg):
        return ctx.guild.get_member_named(
            Search(arg, [m.display_name for m in ctx.guild.members()].best(min_accuracy=0.75))
        )


class GottenGuild(Converter):
    async def convert(self, ctx, arg):
        try:
            return ctx.bot.get_guild(arg)
        except ValueError:
            return None


class Command(Converter):
    async def convert(self, ctx, arg):
        # False indicates command doesn't exist.
        return ctx.bot.get_command(arg) or False
