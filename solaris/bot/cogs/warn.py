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

import time
import typing as t
from string import ascii_lowercase

import discord
from discord.ext import commands

from solaris.utils import checks, chron, string

MODULE_NAME = "warn"

MIN_POINTS = 1
MAX_POINTS = 20
MAX_WARNTYPE_LENGTH = 25
MAX_WARNTYPES = 25


class Warn(commands.Cog):
    """A system to serve official warnings to members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.configurable: bool = True

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.group(name="warn", invoke_without_command=True, help="Warns one or more members in your server.")
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_warn()
    async def warn_group(
        self,
        ctx,
        targets: commands.Greedy[discord.Member],
        warn_type: str,
        points_override: t.Optional[int],
        *,
        comment: t.Optional[str],
    ):
        if not targets:
            return await ctx.send(f"{self.bot.cross} No valid targets were passed.")

        if any(c not in ascii_lowercase for c in warn_type):
            return await ctx.send(f"{self.bot.cross} Warn type identifiers can only contain lower case letters.")

        if (points_override is not None) and (not MIN_POINTS <= points_override <= MAX_POINTS):
            return await ctx.send(
                f"{self.bot.cross} The specified points override must be between {MIN_POINTS} and {MAX_POINTS} inclusive."
            )

        if (comment is not None) and len(comment) > 255:
            return await ctx.send(f"{self.bot.cross} The comment must not exceed 255 characters in length.")

        type_map = {
            warn_type: points
            for warn_type, points in await self.bot.db.records(
                "SELECT WarnType, Points FROM warntypes WHERE GuildID = ?", ctx.guild.id
            )
        }

        if warn_type not in type_map.keys():
            return await ctx.send(f"{self.bot.cross} That warn type does not exist.")

        for target in targets:
            if target.bot:
                await ctx.send(f"{self.bot.info} Skipping {target.display_name} as bots can not be warned.")
                continue

            await self.bot.db.execute(
                "INSERT INTO warns (WarnID, GuildID, UserID, ModID, WarnType, Points, Comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
                self.bot.generate_id(),
                ctx.guild.id,
                target.id,
                ctx.author.id,
                warn_type,
                points_override or type_map[warn_type],
                comment,
            )

            records = await self.bot.db.records(
                "SELECT WarnType, Points FROM warns WHERE GuildID = ? AND UserID = ?", ctx.guild.id, target.id
            )
            max_points, max_strikes = (
                await self.bot.db.record("SELECT MaxPoints, MaxStrikes FROM warn WHERE GuildID = ?", ctx.guild.id)
                or [None] * 2
            )

            if (wc := [r[0] for r in records].count(warn_type)) >= (max_strikes or 3):
                # Account for unbans.
                await target.ban(reason=f"Received {string.ordinal(wc)} warning for {warn_type}.")
                return await ctx.send(
                    f"{self.bot.info} {target.display_name} was banned because they received a {string.ordinal(wc)} warning for the same offence."
                )

            points = sum(r[1] for r in records)

            if points >= (max_points or 12):
                await target.ban(reason=f"Received equal to or more than the maximum allowed number of points.")
                return await ctx.send(
                    f"{self.bot.info} {target.display_name} was banned because they received equal to or more than the maximum allowed number of points."
                )

            await ctx.send(
                f"{target.mention}, you have been warned for {warn_type} for the {string.ordinal(wc)} of {max_strikes or 3} times. You now have {points} of your allowed {max_points or 12} points."
            )

    @warn_group.command(name="remove", aliases=["rm"], help="Removes a warning.")
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_warn()
    async def warn_remove_command(self, ctx, warn_id: str):
        modified = await self.bot.db.execute("DELETE FROM warns WHERE WarnID = ?", warn_id)

        if not modified:
            return await ctx.send(f"{self.bot.cross} That warn ID is not valid.")

        await ctx.send(f"{self.bot.tick} Warn {warn_id} removed.")

    @warn_group.command(name="reset", help="Resets a member's warnings.")
    @checks.module_has_initialised(MODULE_NAME)
    @commands.has_permissions(administrator=True)
    async def warn_reset_command(self, ctx, target: discord.Member):
        modified = await self.bot.db.execute(
            "DELETE FROM warns WHERE GuildID = ? AND UserID = ?", ctx.guild.id, target.id
        )

        if not modified:
            return await ctx.send(f"{self.bot.cross} That member does not have any warns.")

        await ctx.send(f"{self.bot.tick} Warnings for {target.display_name} reset.")

    @warn_group.command(name="list", help="Lists a member's warnings.")
    @checks.module_has_initialised(MODULE_NAME)
    async def warn_list_command(self, ctx, target: t.Optional[t.Union[discord.Member, str]]):
        target = target or ctx.author

        if isinstance(target, str):
            return await ctx.send(
                f"{self.bot.cross} Solaris was unable to identify a member with the information provided."
            )

        records = await self.bot.db.records(
            "SELECT WarnID, ModID, WarnTime, WarnType, Points, Comment FROM warns WHERE GuildID = ? AND UserID = ? ORDER BY WarnTime DESC",
            ctx.guild.id,
            target.id,
        )
        points = sum(record[4] for record in records)

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Warn",
                title=f"Warn information for {target.display_name}",
                description=f"{points} point(s) accumulated. Showing {min(len(records), 10)} of {len(records)} warning(s).",
                colour=target.colour,
                thumbnail=target.avatar_url,
                fields=(
                    (
                        record[0],
                        f"**{record[3]}**: {record[5] or 'No additional comment was made.'} ({record[4]} point(s))\n"
                        f"{getattr(ctx.guild.get_member(record[1]), 'mention', 'Unknown')} - {chron.short_date_and_time(chron.from_iso(record[2]))}",
                        False,
                    )
                    for record in records[-10:]
                ),
            )
        )

    @commands.group(
        name="warntype",
        invoke_without_command=True,
        help="Manages warn types. Use the command for information on available subcommands.",
    )
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_configure()
    async def warntype_group(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        cmds = tuple(sorted(self.bot.get_command("warntype").commands, key=lambda c: c.name))

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Warn",
                description="There are a few different commands you can use to manage warn types.",
                fields=(
                    *(
                        (
                            cmd.name.title(),
                            f"{cmd.help} For more infomation, use `{prefix}help warntype {cmd.name}`",
                            False,
                        )
                        for cmd in cmds
                    ),
                ),
            )
        )

    @warntype_group.command(name="new", help="Creates a new warn type.")
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_configure()
    async def warntype_new_command(self, ctx, warn_type: str, points: int):
        if any(c not in ascii_lowercase for c in warn_type):
            return await ctx.send(f"{self.bot.cross} Warn type identifiers can only contain lower case letters.")

        if len(warn_type) > MAX_WARNTYPE_LENGTH:
            return await ctx.send(
                f"{self.bot.cross} Warn type identifiers must not exceed {MAX_WARNTYPE_LENGTH} characters in length."
            )

        if not MIN_POINTS <= points <= MAX_POINTS:
            return await ctx.send(
                f"{self.bot.cross} The number of points for this warn type must be between {MIN_POINTS} and {MAX_POINTS} inclusive."
            )

        warn_types = await self.bot.db.column("SELECT WarnType FROM warntypes WHERE GuildID = ?", ctx.guild.id)

        if len(warn_types) == MAX_WARNTYPES:
            return await ctx.send(f"{self.bot.cross} You can only set up to {MAX_WARNTYPES} warn types.")

        if warn_type in warn_types:
            prefix = await self.bot.prefix(ctx.guild)
            return await ctx.send(
                f"{self.bot.cross} That warn type already exists. You can use `{prefix}warntype edit {warn_type}`"
            )

        await self.bot.db.execute(
            "INSERT INTO warntypes (GuildID, WarnType, Points) VALUES (?, ?, ?)", ctx.guild.id, warn_type, points
        )
        await ctx.send(
            f'{self.bot.tick} The warn type "{warn_type}" has been created, and is worth {points} point(s).'
        )

    @warntype_group.command(
        name="edit",
        help="Edits an existing warn type. Existing warn records are updated to reflect the changes, but action is not retroactively taken based on point values.",
    )
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_configure()
    async def warntype_edit_command(self, ctx, warn_type: str, new_points: t.Optional[int], new_name: t.Optional[str]):
        if new_points is None and new_name is None:
            await ctx.send(f"{self.bot.cross} Nothing to modify.")

        if new_points is not None:
            if not MIN_POINTS <= new_points <= MAX_POINTS:
                return await ctx.send(
                    f"{self.bot.cross} The number of points for this warn type must be between {MIN_POINTS} and {MAX_POINTS} inclusive."
                )

        if new_name is not None:
            if any(c not in ascii_lowercase for c in new_name):
                return await ctx.send(f"{self.bot.cross} Warn type identifiers can only contain lower case letters.")

            if new_name == warn_type:
                return await ctx.send(f'{self.bot.cross} That warn type "{new_name}" already exists.')

            warn_types = await self.bot.db.column("SELECT WarnType FROM warntypes WHERE GuildID = ?", ctx.guild.id)

            if warn_type not in warn_types:
                return await ctx.send(f'{self.bot.cross} The warn type "{warn_type}" does not exist.')

            if new_name in warn_types:
                return await ctx.send(f'{self.bot.cross} That warn type "{new_name}" already exists.')

        if new_name and new_points:
            if await self.bot.db.field("SELECT RetroUpdates FROM warn WHERE GuildID = ?", ctx.guild.id):
                default = await self.bot.db.field(
                    "SELECT Points FROM warntypes WHERE GuildID = ? AND WarnType = ?", ctx.guild.id, warn_type
                )
                await self.bot.db.execute(
                    "UPDATE warns SET WarnType = ?, Points = ? WHERE GuildID = ? AND WarnType = ? AND Points = ?",
                    new_name,
                    new_points,
                    ctx.guild.id,
                    warn_type,
                    default,
                )
            else:
                await self.bot.db.execute(
                    "UPDATE warns SET WarnType = ? WHERE GuildID = ? AND WarnType = ?",
                    new_name,
                    ctx.guild.id,
                    warn_type,
                )
        elif new_name:
            await self.bot.db.execute(
                "UPDATE warntypes SET WarnType = ? WHERE GuildID = ? AND WarnType = ?",
                new_name,
                ctx.guild.id,
                warn_type,
            )
            await self.bot.db.execute(
                "UPDATE warns SET WarnType = ? WHERE GuildID = ? AND WarnType = ?", new_name, ctx.guild.id, warn_type
            )
            await ctx.send(f'{self.bot.tick} The warn type "{warn_type}" has been renamed to "{new_name}".')
        elif new_points:
            if await self.bot.db.field("SELECT RetroUpdates FROM warn WHERE GuildID = ?", ctx.guild.id):
                default = await self.bot.db.field(
                    "SELECT Points FROM warntypes WHERE GuildID = ? AND WarnType = ?", ctx.guild.id, warn_type
                )
                await self.bot.db.execute(
                    "UPDATE warns SET Points = ? WHERE GuildID = ? AND WarnType = ? AND Points = ?",
                    new_points,
                    ctx.guild.id,
                    warn_type,
                    default,
                )
            await self.bot.db.execute(
                "UPDATE warntypes SET Points = ? WHERE GuildID = ? AND WarnType = ?",
                new_points,
                ctx.guild.id,
                warn_type,
            )
            await ctx.send(f'{self.bot.tick} The warn type "{warn_type}" is now worth {new_points} point(s).')

    @warntype_group.command(
        name="delete",
        aliases=["del"],
        help="Deletes a warn type. Existing warn records are updated to reflect the changes, but action is not retroactively taken based on point values.",
    )
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_configure()
    async def warntype_delete_command(self, ctx, warn_type: str):
        if any(c not in ascii_lowercase for c in warn_type):
            return await ctx.send("Warn types can only contain lower case letters.")

        modified = await self.bot.db.execute(
            "DELETE FROM warntypes WHERE GuildID = ? AND WarnType = ?", ctx.guild.id, warn_type
        )

        if not modified:
            return await ctx.send(f"{self.bot.cross} That warn type does not exist.")

        await self.bot.db.execute("DELETE FROM warns WHERE GuildID = ? AND WarnType = ?", ctx.guild.id, warn_type)
        await ctx.send(f'{self.bot.tick} Warn type "{warn_type}" deleted.')

    @warntype_group.group(name="list", help="Lists the server's warn types.")
    @checks.module_has_initialised(MODULE_NAME)
    @checks.author_can_warn()
    async def warntype_list_command(self, ctx):
        records = await self.bot.db.records("SELECT WarnType, Points FROM warntypes WHERE GuildID = ?", ctx.guild.id)

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Warn",
                title="Warn types",
                description=f"Using {len(records)} of this server's allowed {MAX_WARNTYPES} warn types.",
                thumbnail=ctx.guild.icon_url,
                fields=((warn_type, f"{points} point(s)", True) for warn_type, points in records),
            )
        )


def setup(bot):
    bot.add_cog(Warn(bot))
