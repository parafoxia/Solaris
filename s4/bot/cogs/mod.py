import re
import typing as t

import discord
from discord.ext import commands

from s4.utils import chron, converters


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
            await ctx.send(f"{self.bot.cross} No valid targets were passed.")
        else:
            count = 0

            async with ctx.channel.typing():
                for target in targets:
                    try:
                        await target.kick(reason=f"{reason} - Actioned by {ctx.author.name}")
                        count += 1
                    except discord.Forbidden:
                        await ctx.send(
                            f"Failed to kick {target.display_name} as their permission set is superior to S4's."
                        )

                if count > 0:
                    await ctx.send(f"{self.bot.tick} {count:,} member(s) were kicked.")
                else:
                    await ctx.send(f"{self.bot.cross} No members were kicked.")

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
            await ctx.send(f"{self.bot.cross} No valid targets were passed.")
        elif not 0 <= delete_message_days <= 7:
            await ctx.send(
                f"{self.bot.cross} The number of days to delete is outside valid bounds - it should be between 0 and 7 inclusive."
            )
        else:
            count = 0

            async with ctx.channel.typing():
                for target in targets:
                    try:
                        await target.ban(
                            delete_message_days=delete_message_days, reason=f"{reason} - Actioned by {ctx.author.name}"
                        )
                        count += 1
                    except discord.Forbidden:
                        await ctx.send(
                            f"Failed to ban {target.display_name} as their permission set is superior to S4's."
                        )

                if count > 0:
                    await ctx.send(f"{self.bot.tick} {count:,} member(s) were banned.")
                else:
                    await ctx.send(f"{self.bot.cross} No members were banned.")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, ban_members=True)
    async def unban_command(
        self, ctx, targets: commands.Greedy[discord.Member], *, reason: t.Optional[str] = "No reason provided."
    ):
        # TODO: Actually write this.
        await ctx.send("Not implemented.")

    @commands.command(name="clear", aliases=["clr"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def clear_command(self, ctx, scan: int, targets: commands.Greedy[discord.Member]):
        def _check(m):
            return not targets or m.author in targets

        if not 0 < scan <= 100:
            await ctx.send(
                f"{self.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
            )
        else:
            async with ctx.channel.typing():
                await ctx.message.delete()
                cleared = await ctx.channel.purge(limit=scan, check=_check)
                await ctx.send(
                    f"{self.bot.tick} {len(cleared):,} message(s) were deleted.", delete_after=5,
                )

    @commands.command(name="clearchannel", aliases=["clrch"])
    @commands.has_permissions(manage_messages=True, manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def clearchannel_command(
        self, ctx, target: discord.TextChannel, *, reason: t.Optional[str] = "No reason provided."
    ):
        ctx_is_target = ctx.channel == target

        async with ctx.channel.typing():
            await target.clone(reason=f"{reason} - Actioned by {ctx.author.name}")
            await target.delete(reason=f"Channel cleared. - Actioned by {ctx.author.name}")

            if not ctx_is_target:
                await ctx.send(f"{self.bot.tick} Channel cleared.")

    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True, manage_roles=True)
    async def mute_command(
        self, ctx, targets: commands.Greedy[discord.Member], *, reason: t.Optional[str] = "No reason provided."
    ):
        # TODO: Actually write this.
        await ctx.send("Not implemented.")

    @commands.command(name="setnickname", aliases=["setnick"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(send_messages=True, manage_nicknames=True)
    async def setnickname_command(
        self, ctx, target: t.Union[discord.Member, converters.SearchedMember, str], *, nickname: str
    ):
        target = target or ctx.author

        if len(nickname) > 32:
            await ctx.send(f"{self.bot.cross} Nicknames can not be more than 32 characters in length.")
        elif not isinstance(target, discord.Member):
            await ctx.send(f"{self.bot.cross} S4 was unable to identify a server member with the information provided.")
        else:
            try:
                await target.edit(nick=nickname)
                await ctx.send(f"{self.bot.tick} Nickname changed.")
            except discord.Forbidden:
                await ctx.send(f"{self.bot.cross} Failed to change {target.display_name}'s nickname as their permission set is superior to S4's.")

    @commands.command(name="clearnickname", aliases=["clrnick"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(send_messages=True, manage_nicknames=True)
    async def clearnickname_command(self, ctx, targets: commands.Greedy[discord.Member]):
        count = 0

        async with ctx.channel.typing():
            for target in targets:
                try:
                    await target.edit(nick=None)
                    count += 1
                except discord.Forbidden:
                    await ctx.send(f"Failed to clear {target.display_name}'s nickname as their permission set is superior to S4's.")

            if count > 0:
                await ctx.send(f"{self.bot.tick} Cleared {count:,} member(s)' nicknames.")
            else:
                await ctx.send(f"{self.bot.cross} No members' nicknames were changed.")

    @commands.command(name="unhoistnicknames")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(send_messages=True, manage_nicknames=True)
    async def unhoistnicknames_command(self, ctx):
        count = 0

        async with ctx.channel.typing():
            for member in ctx.guild.members:
                try:
                    if (match := re.match("[^A-Za-z]+", member.display_name)) is not None:
                        await member.edit(nick=member.display_name.replace(match.group(), "", 1))
                        count += 1
                except discord.Forbidden:
                    pass

            await ctx.send("{self.bot.info} Unhoisted {count:,} nicknames.")


def setup(bot):
    bot.add_cog(Mod(bot))
