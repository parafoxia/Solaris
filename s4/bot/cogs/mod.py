import typing as t

import discord
from discord.ext import commands

from s4.utils import chron


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(send_messages=True, kick_members=True)
    async def kick_command(
        self, ctx, targets: commands.Greedy[discord.Member], *, reason: t.Optional[str] = "No reason provided."
    ):
        if not targets:
            await ctx.send(self.bot.message.load("no targets"))

        else:
            kicks = 0

            async with ctx.channel.typing():
                for target in targets:
                    try:
                        await target.kick(reason=f"{reason} - Actioned by {ctx.author.name}")
                    except discord.Forbidden:
                        await ctx.send(self.bot.message.load("unable to kick", member=target))

                if kicks > 0:
                    await ctx.send(self.bot.message.load("kick success", kicks=kicks))
                else:
                    await ctx.send(self.bot.message.load("kick failed"))

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, ban_members=True)
    async def ban_command(
        self,
        ctx,
        targets: commands.Greedy[discord.Member],
        delete_message_days: t.Optional[int] = 1,
        *,
        reason: t.Optional[str] = "No reason provided.",
    ):
        # NOTE: This is here to get mypy to shut up. Need to look at typehints for this.
        delete_message_days = delete_message_days or 1

        if not targets:
            await ctx.send(self.bot.message.load("no targets"))

        elif not 0 <= delete_message_days <= 7:
            await ctx.send(self.bot.message.load("delete message days outside bounds"))

        else:
            bans = 0

            async with ctx.channel.typing():
                for target in targets:
                    try:
                        await target.kick(reason=f"{reason} - Actioned by {ctx.author.name}")
                    except discord.Forbidden:
                        await ctx.send(self.bot.message.load("unable to ban", member=target))

                if bans > 0:
                    await ctx.send(self.bot.message.load("ban success", bans=bans))
                else:
                    await ctx.send(self.bot.message.load("ban failed"))

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def clear_command(self, ctx, scan: int, targets: commands.Greedy[discord.Member]):
        def _check(m):
            return not targets or m.author in targets

        if not 0 < scan <= 100:
            await ctx.send(self.bot.message.load("scan outside bounds"))

        else:
            async with ctx.channel.typing():
                await ctx.message.delete()
                cleared = await ctx.channel.purge(limit=scan, check=_check)
                await ctx.send(
                    self.bot.message.load("clear success", cleared=len(cleared)), delete_after=5,
                )

    @commands.command(name="clearchannel")
    @commands.has_permissions(manage_messages=True, manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def clearchannel_command(
        self, ctx, target: discord.TextChannel, *, reason: t.Optional[str] = "No reason provided."
    ):
        async with ctx.channel.typing():
            await target.clone(reason=f"{reason} - Actioned by {ctx.author.name}")
            await target.delete(reason=f"Channel cleared. - Actioned by {ctx.author.name}")
            # TODO: Set this to the log channel.
            # await ctx.send(self.bot.message.load("clear channel success"))

    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True, manage_roles=True)
    async def mute_command(
        self, ctx, targets: commands.Greedy[discord.Member], *, reason: t.Optional[str] = "No reason provided."
    ):
        # TODO: Actually write this.
        await ctx.send("Not implemented.")


def setup(bot):
    bot.add_cog(Mod(bot))
