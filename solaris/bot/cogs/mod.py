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

import datetime as dt
import re
import typing as t

import discord
from discord.ext import commands

from solaris.utils import chron, converters

UNHOIST_PATTERN = "".join(chr(i) for i in [*range(0x20, 0x30), *range(0x3A, 0x41), *range(0x5B, 0x61)])
STRICT_UNHOIST_PATTERN = "".join(chr(i) for i in [*range(0x20, 0x41), *range(0x5B, 0x61)])


class Mod(commands.Cog):
    """Basic moderation actions designed to help you keep your server clean and safe."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="kick", help="Kicks one or more members from your server.")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(send_messages=True, kick_members=True)
    async def kick_command(
        self, ctx, targets: commands.Greedy[discord.Member], *, reason: t.Optional[str] = "No reason provided."
    ):
        if not targets:
            await ctx.send(f"{self.bot.cross} No valid targets were passed.")
        else:
            count = 0

            async with ctx.typing():
                for target in targets:
                    try:
                        await target.kick(reason=f"{reason} - Actioned by {ctx.author.name}")
                        count += 1
                    except discord.Forbidden:
                        await ctx.send(
                            f"Failed to kick {target.display_name} as their permission set is superior to Solaris'."
                        )

                if count > 0:
                    await ctx.send(f"{self.bot.tick} {count:,} member(s) were kicked.")
                else:
                    await ctx.send(f"{self.bot.cross} No members were kicked.")

    @commands.command(
        name="ban",
        help="Bans one or more members from your server. If you have a user's ID, you can ban them regardless of whether or not they are currently in the server.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, ban_members=True)
    async def ban_command(
        self,
        ctx,
        targets: commands.Greedy[t.Union[discord.Member, converters.User]],
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

            async with ctx.typing():
                for target in targets:
                    try:
                        await ctx.guild.ban(
                            target,
                            delete_message_days=delete_message_days,
                            reason=(
                                (f"{reason}" if target in ctx.guild.members else f"{reason} (Hackban)")
                                + f" - Actioned by {ctx.author.name}"
                            ),
                        )
                        count += 1
                    except discord.Forbidden:
                        await ctx.send(
                            f"Failed to ban {target.display_name} as their permission set is superior to Solaris'."
                        )

                if count > 0:
                    await ctx.send(f"{self.bot.tick} {count:,} member(s) were banned.")
                else:
                    await ctx.send(f"{self.bot.cross} No members were banned.")

    @commands.command(
        name="unban",
        help="Unbans one or more users from your server. You can provide either an ID or a username and discriminator or users you wish to unban - attempting to mention users will not work.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(send_messages=True, ban_members=True)
    async def unban_command(
        self, ctx, targets: commands.Greedy[converters.BannedUser], *, reason: t.Optional[str] = "No reason provided."
    ):
        if not targets:
            await ctx.send(f"{self.bot.cross} No valid targets were passed.")
        else:
            count = 0

            async with ctx.typing():
                for target in targets:
                    await ctx.guild.unban(target, reason=f"{reason} - Actioned by {ctx.author.name}")
                    count += 1

                if count > 0:
                    await ctx.send(f"{self.bot.tick} {count:,} user(s) were unbanned.")
                else:
                    await ctx.send(f"{self.bot.cross} No users were unbanned.")

    @commands.command(name="clear", aliases=["clr"], help="Clears up to 100 messages from a channel.")
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
            async with ctx.typing():
                await ctx.message.delete()
                cleared = await ctx.channel.purge(
                    limit=scan, check=_check, after=dt.datetime.utcnow() - dt.timedelta(days=14)
                )
                await ctx.send(
                    f"{self.bot.tick} {len(cleared):,} message(s) were deleted.", delete_after=5,
                )

    @commands.command(
        name="clearchannel",
        aliases=["clrch"],
        help="Clears an entire channel of messages. Solaris does this by cloning the given channel, and then deleting it, keeping the clean clone intact.",
    )
    @commands.has_permissions(manage_messages=True, manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def clearchannel_command(
        self, ctx, target: discord.TextChannel, *, reason: t.Optional[str] = "No reason provided."
    ):
        ctx_is_target = ctx.channel == target

        async with ctx.typing():
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

    @commands.command(name="setnickname", aliases=["setnick"], help="Sets a member's nickname.")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(send_messages=True, manage_nicknames=True)
    async def setnickname_command(
        self, ctx, target: t.Union[discord.Member, converters.SearchedMember, str], *, nickname: str
    ):
        target = target or ctx.author

        if len(nickname) > 32:
            await ctx.send(f"{self.bot.cross} Nicknames can not be more than 32 characters in length.")
        elif not isinstance(target, discord.Member):
            await ctx.send(
                f"{self.bot.cross} Solaris was unable to identify a server member with the information provided."
            )
        else:
            try:
                await target.edit(nick=nickname)
                await ctx.send(f"{self.bot.tick} Nickname changed.")
            except discord.Forbidden:
                await ctx.send(
                    f"{self.bot.cross} Failed to change {target.display_name}'s nickname as their permission set is superior to Solaris'."
                )

    @commands.command(name="clearnickname", aliases=["clrnick"], help="Clears one or more members' nicknames.")
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(send_messages=True, manage_nicknames=True)
    async def clearnickname_command(
        self, ctx, targets: commands.Greedy[discord.Member], *, reason: t.Optional[str] = "No reason provided."
    ):
        count = 0

        async with ctx.typing():
            for target in targets:
                try:
                    await target.edit(nick=None, reason=f"{reason} - Actioned by {ctx.author.name}")
                    count += 1
                except discord.Forbidden:
                    await ctx.send(
                        f"Failed to clear {target.display_name}'s nickname as their permission set is superior to Solaris'."
                    )

            if count > 0:
                await ctx.send(f"{self.bot.tick} Cleared {count:,} member(s)' nicknames.")
            else:
                await ctx.send(f"{self.bot.cross} No members' nicknames were changed.")

    @commands.command(
        name="unhoistnicknames", cooldown_after_parsing=True, help="Unhoists the nicknames of all members.",
    )
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(send_messages=True, manage_nicknames=True)
    async def unhoistnicknames_command(self, ctx, *, strict: t.Optional[bool] = False):
        count = 0

        async with ctx.typing():
            for member in ctx.guild.members:
                try:
                    match = re.match(
                        rf"[{STRICT_UNHOIST_PATTERN if strict else UNHOIST_PATTERN}]+", member.display_name
                    )
                    if match is not None:
                        await member.edit(
                            nick=member.display_name.replace(match.group(), "", 1),
                            reason=f"Unhoisted. - Actioned by {ctx.author.name}",
                        )
                        count += 1
                except discord.Forbidden:
                    pass

            await ctx.send(f"{self.bot.info} Unhoisted {count:,} nicknames.")

    @commands.group(
        name="delete",
        aliases=["del", "rm"],
        invoke_without_command=True,
        help="Deletes items in singular or batches. Use the command for information on available subcommands.",
    )
    async def delete_group(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        cmds = tuple(sorted(self.bot.get_command("delete").commands, key=lambda c: c.name))

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Delete",
                description="There are a few different deletion methods you can use.",
                fields=(
                    *(
                        (
                            cmd.name.title(),
                            f"{cmd.help} For more infomation, use `{prefix}help delete {cmd.name}`",
                            False,
                        )
                        for cmd in cmds
                    ),
                ),
            )
        )

    @delete_group.command(name="channel", cooldown_after_parsing=True, help="Deletes the specified channel.")
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def delete_channel_command(
        self,
        ctx,
        target: t.Union[discord.TextChannel, discord.VoiceChannel],
        *,
        reason: t.Optional[str] = "No reason provided.",
    ):
        ctx_is_target = ctx.channel == target

        async with ctx.typing():
            await target.delete(reason=f"{reason} - Actioned by {ctx.author.name}")

            if not ctx_is_target:
                await ctx.send(f"{self.bot.tick} Channel deleted.")

    @delete_group.command(
        name="channels",
        cooldown_after_parsing=True,
        help="Deletes one or more channels. Unlike `delete channel`, this can only be used by server administrators.",
    )
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def delete_channels_command(
        self,
        ctx,
        targets: commands.Greedy[t.Union[discord.TextChannel, discord.VoiceChannel]],
        *,
        reason: t.Optional[str] = "No reason provided.",
    ):
        if not targets:
            await ctx.send(f"{self.bot.cross} No valid targets were passed.")
        else:
            ctx_in_targets = ctx.channel in targets
            count = 0

            async with ctx.typing():
                for target in targets:
                    await target.delete(reason=f"{reason} - Actioned by {ctx.author.name}")
                    count += 1

            if not ctx_in_targets:
                await ctx.send(f"{self.bot.tick} {count:,} channel(s) were deleted.")

    @delete_group.command(
        name="category",
        cooldown_after_parsing=True,
        help="Deletes the specified category along with all channels within it.",
    )
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def delete_category_command(
        self, ctx, target: discord.CategoryChannel, *, reason: t.Optional[str] = "No reason provided."
    ):
        ctx_in_targets = ctx.channel in target.text_channels

        async with ctx.typing():
            for tc in target.channels:
                await tc.delete(reason=f"{reason} - Actioned by {ctx.author.name}")
            await target.delete(reason=f"{reason} - Actioned by {ctx.author.name}")

            if not ctx_in_targets:
                await ctx.send(f"{self.bot.tick} Category deleted.")

    @delete_group.command(name="role", cooldown_after_parsing=True, help="Deletes the specified role.")
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True, manage_roles=True)
    async def delete_role_command(
        self, ctx, target: discord.Role, *, reason: t.Optional[str] = "No reason provided.",
    ):
        async with ctx.typing():
            await target.delete(reason=f"{reason} - Actioned by {ctx.author.name}")

            await ctx.send(f"{self.bot.tick} Role deleted.")

    @delete_group.command(
        name="roles",
        cooldown_after_parsing=True,
        help="Deletes one or more roles. Unlike `delete role`, this can only be used by server administrators.",
    )
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(send_messages=True, manage_channels=True)
    async def delete_roles_command(
        self, ctx, targets: commands.Greedy[discord.Role], *, reason: t.Optional[str] = "No reason provided.",
    ):
        if not targets:
            await ctx.send(f"{self.bot.cross} No valid targets were passed.")
        else:
            count = 0

            async with ctx.typing():
                for target in targets:
                    await target.delete(reason=f"{reason} - Actioned by {ctx.author.name}")
                    count += 1

            await ctx.send(f"{self.bot.tick} {count:,} role(s) were deleted.")


def setup(bot):
    bot.add_cog(Mod(bot))
