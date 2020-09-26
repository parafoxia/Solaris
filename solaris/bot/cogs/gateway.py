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
import typing as t
from collections import defaultdict

import discord
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from solaris.utils import checks, chron, string, trips

MODULE_NAME = "gateway"


class Okay:
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild

    async def permissions(self):
        if not self.guild.me.guild_permissions.manage_roles:
            await trips.gateway(self, "Solaris no longer has the Manage Roles permission")
        elif not self.guild.me.guild_permissions.kick_members:
            await trips.gateway(self, "Solaris no longer has the Kick Members permission")
        else:
            return True

    async def gate_message(self, rc_id, gm_id):
        try:
            if (rc := self.bot.get_channel(rc_id)) is None:
                await trips.gateway(self, "the rules channel no longer exists, or is unable to be accessed by Solaris")
            else:
                # This is done here to ensure the correct order of operations.
                gm = await rc.fetch_message(gm_id)

                if not rc.permissions_for(self.guild.me).manage_messages:
                    await trips.gateway(
                        self, "Solaris does not have the Manage Messages permission in the rules channel"
                    )
                else:
                    return gm

        except discord.NotFound:
            await trips.gateway(self, "the gate message no longer exists")

    async def blocking_role(self, br_id):
        if (br := self.guild.get_role(br_id)) is None:
            await trips.gateway(self, "the blocking role no longer exists, or is unable to be accessed by Solaris")
        elif br.position >= self.guild.me.top_role.position:
            await trips.gateway(
                self, "the blocking role is equal to or higher than Solaris' top role in the role hierarchy"
            )
        else:
            return br

    async def member_roles(self, mr_ids):
        if mr_ids is not None:
            for r in (mrs := [self.guild.get_role(int(id_)) for id_ in mr_ids.split(",")]) :
                if r is None:
                    await trips.gateway(
                        self, "one or more member roles no longer exist, or are unable to be accessed by Solaris"
                    )
                    return
                elif r.position >= self.guild.me.top_role.position:
                    await trips.gateway(
                        self,
                        "one or more member roles are equal to or higher than Solaris' top role in the role hierarchy",
                    )
                    return

            return mrs

    async def exception_roles(self, er_ids):
        if er_ids is not None:
            for r in (ers := [self.guild.get_role(int(id_)) for id_ in er_ids.split(",")]) :
                if r is None:
                    await trips.gateway(
                        self, "one or more exception roles no longer exist, or are unable to be accessed by Solaris"
                    )
                    return

            return ers

    async def welcome_channel(self, wc_id):
        if wc_id is not None:
            if (wc := self.bot.get_channel(wc_id)) is None:
                await trips.gateway(
                    self, "the welcome channel no longer exists or is unable to be accessed by Solaris"
                )
            elif not wc.permissions_for(self.guild.me).send_messages:
                await trips.gateway(self, "Solaris does not have the Send Messages permission in the welcome channel")
            else:
                return wc

    async def goodbye_channel(self, gc_id):
        if gc_id is not None:
            if (gc := self.bot.get_channel(gc_id)) is None:
                await trips.gateway(
                    self, "the goodbye channel no longer exists or is unable to be accessed by Solaris"
                )
            elif not gc.permissions_for(self.guild.me).send_messages:
                await trips.gateway(self, "Solaris does not have the Send Messages permission in the goodbye channel")
            else:
                return gc


class Synchronise:
    def __init__(self, bot):
        self.bot = bot

    async def _allow(self, okay, member, br_id, mr_ids):
        if (mrs := await okay.member_roles(mr_ids)) and (unassigned := set(mrs) - set(member.roles)):
            await member.add_roles(
                *list(unassigned),
                reason="Member accepted the server rules (performed during synchronisation).",
                atomic=False,
            )

        if (br := await okay.blocking_role(br_id)) in member.roles:
            await member.remove_roles(
                br,
                reason="Member accepted the server rules, or was given an exception role (performed during synchronisation).",
            )

    async def _deny(self, okay, member, br_id):
        await member.kick(reason="Member declined the server rules (performed during synchronisation).")

    async def members(self, guild, okay, gm, br_id, mr_ids, er_ids, last_commit, entrants, accepted):
        def _check(m):
            return not m.bot and (m.joined_at > last_commit or m.id in entrants)

        reacted = []
        new = []
        left = []

        ticked = await gm.reactions[0].users().flatten()
        crossed = await gm.reactions[1].users().flatten()
        ers = await okay.exception_roles(er_ids) or []

        for member in filter(lambda m: _check(m), guild.members):
            if member in ticked:
                await self._allow(okay, member, br_id, mr_ids)
                reacted.append((guild.id, member.id))
                new.append((guild.id, member.id))
            elif member in crossed:
                await self._deny(okay, member, br_id)
                reacted.append((guild.id, member.id))
            elif any(r in member.roles for r in ers):
                await self._allow(okay, member, br_id, mr_ids)
                reacted.append((guild.id, member.id))

        for user_id in set([*entrants, *accepted]):
            if not guild.get_member(user_id):
                left.append((guild.id, user_id))

        await self.bot.db.executemany("DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", set([*reacted, *left]))
        await self.bot.db.executemany("DELETE FROM accepted WHERE GuildID = ? AND UserID = ?", set(left))
        await self.bot.db.executemany("INSERT OR IGNORE INTO accepted VALUES (?, ?)", set(new))

    async def roles(self, guild, okay, br_id, mr_ids, accepted, accepted_only):
        def _check(m):
            return not m.bot and (not accepted_only or m.id in accepted)

        br = await okay.blocking_role(br_id)
        mrs = await okay.member_roles(mr_ids)

        for member in filter(lambda m: _check(m), guild.members):
            if br not in member.roles and (unassigned := set(mrs) - set(member.roles)):
                await member.add_roles(
                    *list(unassigned),
                    reason="Member roles have been updated (performed during synchronisation).",
                    atomic=False,
                )

    async def reactions(self, guild, gm, accepted):
        tick = gm.reactions[0]
        cross = gm.reactions[1]
        ticked = await tick.users().flatten()
        crossed = await cross.users().flatten()
        ticked_and_left = set(ticked) - set(guild.members)
        crossed_and_left = set(crossed) - set(guild.members)

        for user in ticked_and_left:
            await gm.remove_reaction(tick.emoji, user)

        for user in crossed_and_left:
            await gm.remove_reaction(cross.emoji, user)

        for user in crossed:
            if user.id in accepted:
                await gm.remove_reaction(cross.emoji, user)

    async def on_boot(self):
        last_commit = chron.from_iso(await self.bot.db.field("SELECT Value FROM bot WHERE Key = 'last commit'"))
        records = await self.bot.db.records(
            "SELECT GuildID, RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE Active = 1"
        )

        entrants = {
            guild_id: [int(user_id) for user_id in user_ids.split(",")]
            for guild_id, user_ids in await self.bot.db.records(
                "SELECT GuildID, GROUP_CONCAT(UserID) FROM entrants GROUP BY GuildID"
            )
        }

        accepted = {
            guild_id: [int(user_id) for user_id in user_ids.split(",")]
            for guild_id, user_ids in await self.bot.db.records(
                "SELECT GuildID, GROUP_CONCAT(UserID) FROM accepted GROUP BY GuildID"
            )
        }

        for guild_id, rc_id, gm_id, br_id, mr_ids, er_ids in records:
            guild = self.bot.get_guild(guild_id)
            okay = Okay(self.bot, guild)

            if gm := await okay.gate_message(rc_id, gm_id):
                await self.members(
                    guild,
                    okay,
                    gm,
                    br_id,
                    mr_ids,
                    er_ids,
                    last_commit,
                    entrants.get(guild_id, []),
                    accepted.get(guild_id, []),
                )

        await self.bot.db.execute("UPDATE entrants SET Timeout = datetime('now', '+3600 seconds')")


class Gateway(commands.Cog):
    """Controls and monitors the flow of members in and out of your server. When active, members are forced to accept the server rules before gaining full access to the server."""

    def __init__(self, bot):
        self.bot = bot
        self.bot.scheduler.add_job(self.remove_on_timeout, CronTrigger(second=0))
        self.configurable = True

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            await Synchronise(self.bot).on_boot()
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.bot.ready.gateway:
            okay = Okay(self.bot, member.guild)
            active, br_id, wc_id, timeout, wbt = (
                await self.bot.db.record(
                    "SELECT Active, BlockingRoleID, WelcomeChannelID, Timeout, WelcomeBotText FROM gateway WHERE GuildID = ?",
                    member.guild.id,
                )
                or [None] * 7
            )

            if active and await okay.permissions():
                if member.bot:
                    if wc := await okay.welcome_channel(wc_id):
                        await wc.send(
                            self.format_custom_message(wbt, member)
                            or f"‎The bot {member.mention} was added to the server."
                        )
                else:
                    if br := await okay.blocking_role(br_id):
                        await member.add_roles(br, reason="Needed to enforce a decision on the server rules.")
                        await self.bot.db.execute(
                            "INSERT INTO entrants VALUES (?, ?, ?)",
                            member.guild.id,
                            member.id,
                            chron.to_iso(member.joined_at + dt.timedelta(seconds=timeout or 300)),
                        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if self.bot.ready.gateway:
            okay = Okay(self.bot, member.guild)
            active, rc_id, gm_id, gc_id, gt, gbt = (
                await self.bot.db.record(
                    "SELECT Active, RulesChannelID, GateMessageID, GoodbyeChannelID, GoodbyeText, GoodbyeBotText FROM gateway WHERE GuildID = ?",
                    member.guild.id,
                )
                or [None] * 4
            )

            if active:
                if member.bot:
                    if gc := await okay.goodbye_channel(gc_id):
                        await gc.send(
                            self.format_custom_message(gbt, member)
                            or f'‎The bot "{member.display_name}" was removed from the server.'
                        )
                else:
                    if await self.bot.db.field(
                        "SELECT UserID FROM entrants WHERE GuildID = ? AND UserID = ?", member.guild.id, member.id
                    ):
                        await self.bot.db.execute(
                            "DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", member.guild.id, member.id
                        )
                    elif gc := await okay.goodbye_channel(gc_id):
                        await gc.send(
                            self.format_custom_message(gt, member)
                            or f"‎{member.display_name} is no longer in the server."
                        )

                    await self.bot.db.execute(
                        "DELETE FROM accepted WHERE GuildID = ? AND UserID = ?", member.guild.id, member.id
                    )

                    if (gm := await okay.gate_message(rc_id, gm_id)) :
                        for emoji in self.bot.emoji.get_many("confirm", "cancel"):
                            try:
                                await gm.remove_reaction(emoji, member)
                            except discord.NotFound:
                                # In the rare instance the module trips while attempting to remove a reaction.
                                pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if self.bot.ready.gateway and len(after.roles) > len(before.roles):
            okay = Okay(self.bot, after.guild)
            active, br_id, mr_ids, er_ids = (
                await self.bot.db.record(
                    "SELECT Active, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE GuildID = ?",
                    after.guild.id,
                )
                or [None] * 4
            )

            if active and er_ids:
                added_role = (set(after.roles) - set(before.roles)).pop()

                ers = await okay.exception_roles(er_ids)
                if ers is not None and added_role in ers:
                    await self.allow_on_exception(after, okay, br_id, mr_ids)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.bot.ready.gateway:
            okay = Okay(self.bot, payload.member.guild)
            active, rc_id, gm_id, br_id, mr_ids, wc_id, wt = (
                await self.bot.db.record(
                    "SELECT Active, RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, WelcomeChannelID, WelcomeText FROM gateway WHERE GuildID = ?",
                    payload.guild_id,
                )
                or [None] * 7
            )

            if active and payload.message_id == gm_id and (gm := await okay.gate_message(rc_id, gm_id)):
                if payload.emoji.id == self.bot.emoji.get("confirm").id:
                    await self.allow_on_accept(payload.member, okay, br_id, mr_ids, wc_id, wt)
                elif payload.emoji.id == self.bot.emoji.get("cancel").id:
                    await self.remove_on_decline(payload.member, okay, br_id)

    @staticmethod
    def format_custom_message(text, member):
        if text:
            bot_count = len([m for m in member.guild.members if m.bot])
            human_count = member.guild.member_count - bot_count

            # Contains U+200E character.
            return "‎" + string.safe_format(
                text,
                membername=member.name,
                username=member.name,
                membermention=member.mention,
                usermention=member.mention,
                memberstr=str(member),
                userstr=str(member),
                memberid=member.id,
                userid=member.id,
                servername=member.guild.name,
                guildname=member.guild.name,
                serverid=member.guild.id,
                guildid=member.guild.id,
                membercount=member.guild.member_count,
                ordmembercount=string.ordinal(member.guild.member_count),
                humancount=human_count,
                ordhumancount=string.ordinal(human_count),
                botcount=bot_count,
                ordbotcount=string.ordinal(bot_count),
            )

    async def allow_on_accept(self, member, okay, br_id, mr_ids, wc_id, wt):
        if (br := await okay.blocking_role(br_id)) in member.roles:
            if (mrs := await okay.member_roles(mr_ids)) and (unassigned := set(mrs) - set(member.roles)):
                await member.add_roles(*list(unassigned), reason="Member accepted the server rules.", atomic=False)
            await member.remove_roles(br, reason="Member accepted the server rules.")

            if wc := await okay.welcome_channel(wc_id):
                await wc.send(
                    self.format_custom_message(wt, member)
                    or f"‎{member.mention} joined the server and accepted the rules. Welcome!"
                )

            await self.bot.db.execute(
                "DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", member.guild.id, member.id
            )

        await self.bot.db.execute("INSERT OR IGNORE INTO accepted VALUES (?, ?)", member.guild.id, member.id)

    async def remove_on_decline(self, member, okay, br_id):
        if (br := await okay.blocking_role(br_id)) in member.roles:
            await member.kick(reason="Member declined the server rules.")

    async def allow_on_exception(self, member, okay, br_id, mr_ids):
        if (br := await okay.blocking_role(br_id)) in member.roles:
            if (mrs := await okay.member_roles(mr_ids)) and (unassigned := set(mrs) - set(member.roles)):
                await member.add_roles(*list(unassigned), reason="Member was given an exception role.", atomic=False)
            await member.remove_roles(br, reason="Member was given an exception role.")

            await self.bot.db.execute(
                "DELETE FROM entrants WHERE GuildID = ? AND UserID = ?", member.guild.id, member.id
            )

    async def remove_on_timeout(self):
        if self.bot.ready.gateway:
            time_outs = {}

            for guild_id, user_id in await self.bot.db.records(
                "SELECT GuildID, UserID FROM entrants WHERE CURRENT_TIMESTAMP > Timeout"
            ):
                time_outs.setdefault(guild_id, []).append(user_id)

            for guild_id, user_ids in time_outs.items():
                guild = self.bot.get_guild(guild_id)
                br = await Okay(self.bot, guild).blocking_role(
                    await self.bot.db.field("SELECT BlockingRoleID FROM gateway WHERE GuildID = ?", guild_id)
                )

                for user_id in user_ids:
                    if br in (member := guild.get_member(user_id)).roles:
                        await member.kick(reason="Member failed to accept the server rules before being timed out.")

    @commands.group(
        name="synchronise",
        aliases=["synchronize", "sync"],
        invoke_without_command=True,
        help="Synchronise the gateway module. In theory, you should only ever need this as a convenience utility, but it is useful to use if Solaris falls out of sync for whatever reason. Use the command for information on available subcommands.",
    )
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    @checks.author_can_configure()
    async def synchronise_group(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        cmds = tuple(sorted(self.bot.get_command("synchronise").commands, key=lambda c: c.name))

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Synchronise",
                description="There are a few different syncing methods you can use.",
                fields=(
                    *(
                        (
                            cmd.name.title(),
                            f"{cmd.help} For more infomation, use `{prefix}help synchronise {cmd.name}`",
                            False,
                        )
                        for cmd in (*cmds[1:], cmds[0])  # Order them properly.
                    ),
                    (
                        "Why does the module need synchronising?",
                        "Generally speaking, it will not 99% of the time, especially as Solaris performs an automatic synchronisation on start-up. However, due to the complexity of the systems used, and measures taken to make sure there are no database conflicts, it can fall out of sync sometimes. This command is the solution to that problem.",
                        False,
                    ),
                ),
            )
        )

    @synchronise_group.command(
        name="members",
        cooldown_after_parsing=True,
        help="Handles offline arrivals and departures. This is generally not required as Solaris does this on start-up.",
    )
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    @checks.author_can_configure()
    async def synchronise_members_command(self, ctx):
        async with ctx.typing():
            okay = Okay(self.bot, ctx.guild)
            rc_id, gm_id, br_id, mr_ids, er_ids = (
                await self.bot.db.record(
                    "SELECT RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE GuildID = ?",
                    ctx.guild.id,
                )
                or [None] * 5
            )
            last_commit = chron.from_iso(await self.bot.db.field("SELECT Value FROM bot WHERE Key = 'last commit'"))
            entrants = await self.bot.db.column("SELECT UserID FROM entrants WHERE GuildID = ?", ctx.guild.id)
            accepted = await self.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild.id)

            if gm := await okay.gate_message(rc_id, gm_id):
                await Synchronise(self.bot).members(
                    ctx.guild, okay, gm, br_id, mr_ids, er_ids, last_commit, entrants, accepted
                )
                await ctx.send(f"{self.bot.tick} Server members synchronised.")

    @synchronise_group.command(
        name="roles",
        cooldown_after_parsing=True,
        help="Provides the member roles to those who have accepted the rules. This is good to run after you add a new member role, but Solaris will not remove roles that are no longer member roles. If `accepted_only` is set to `False`, every single member will receive these roles regardless of any other factors.",
    )
    @commands.cooldown(1, 3600, commands.BucketType.guild)
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    @checks.author_can_configure()
    async def synchronise_roles_command(self, ctx, accepted_only: t.Optional[bool] = True):
        async with ctx.typing():
            okay = Okay(self.bot, ctx.guild)
            br_id, mr_ids = (
                await self.bot.db.record(
                    "SELECT BlockingRoleID, MemberRoleIDs FROM gateway WHERE GuildID = ?", ctx.guild.id,
                )
                or [None] * 2
            )
            accepted = await self.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild.id)

            await Synchronise(self.bot).roles(ctx.guild, okay, br_id, mr_ids, accepted, accepted_only)
            await ctx.send(f"{self.bot.tick} Member roles synchronised.")

    @synchronise_group.command(
        name="reactions",
        cooldown_after_parsing=True,
        help="Synchronises the reactions on the gate message. This is useful if you only want to view reactions for current members, but as this is an expensive operation in large servers, you can only do this once every 24 hours.",
    )
    @commands.cooldown(1, 86400, commands.BucketType.guild)
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    @checks.author_can_configure()
    async def synchronise_reactions_command(self, ctx):
        async with ctx.typing():
            okay = Okay(self.bot, ctx.guild)
            rc_id, gm_id = (
                await self.bot.db.record(
                    "SELECT RulesChannelID, GateMessageID FROM gateway WHERE GuildID = ?", ctx.guild.id,
                )
                or [None] * 2
            )
            accepted = await self.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild.id)

            if gm := await okay.gate_message(rc_id, gm_id):
                await Synchronise(self.bot).reactions(ctx.guild, gm, accepted)
                await ctx.send(f"{self.bot.tick} Gate message reactions synchronised.")

    @synchronise_group.command(
        name="everything",
        aliases=["full", "all"],
        cooldown_after_parsing=True,
        help="Does all of the above. Read the help descriptions for the other commands in this group for more information.",
    )
    @commands.cooldown(1, 86400, commands.BucketType.guild)
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    @checks.author_can_configure()
    async def synchronise_everything_command(self, ctx, roles_for_accepted_only: t.Optional[bool] = True):
        async with ctx.typing():
            okay = Okay(self.bot, ctx.guild)
            rc_id, gm_id, br_id, mr_ids, er_ids = (
                await self.bot.db.record(
                    "SELECT RulesChannelID, GateMessageID, BlockingRoleID, MemberRoleIDs, ExceptionRoleIDs FROM gateway WHERE GuildID = ?",
                    ctx.guild.id,
                )
                or [None] * 5
            )
            last_commit = chron.from_iso(await self.bot.db.field("SELECT Value FROM bot WHERE Key = 'last commit'"))
            entrants = await self.bot.db.column("SELECT UserID FROM entrants WHERE GuildID = ?", ctx.guild.id)
            accepted = await self.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild.id)

            if gm := await okay.gate_message(rc_id, gm_id):
                sync = Synchronise(self.bot)
                await sync.members(ctx.guild, okay, gm, br_id, mr_ids, er_ids, last_commit, entrants, accepted)
                await sync.roles(ctx.guild, okay, br_id, mr_ids, accepted, roles_for_accepted_only)
                await sync.reactions(ctx.guild, gm, accepted)
                await ctx.send(f"{self.bot.tick} Gateway module fully synchronised.")

    @commands.command(
        name="checkaccepted",
        aliases=["ca"],
        help='Checks whether a given user has accepted the server rules. If no user is provided, Solaris will display the total number of members who have accepted. A member who has "accepted" is taken as one who has reacted to the gate message with the confirm emoji at some point, regardless of whether they unreacted later. The only exceptions to this are if the member leaves the server, or if the acceptance records are manually reset.',
    )
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    async def checkaccepted_command(self, ctx, target: t.Optional[discord.Member]):
        if target is not None:
            if await self.bot.db.field(
                "SELECT UserID FROM accepted WHERE GuildID = ? AND UserID = ?", target.guild.id, target.id
            ):
                await ctx.send(f"{self.bot.tick} {target.display_name} has accepted the server rules.")
            else:
                await ctx.send(f"{self.bot.cross} {target.display_name} has not accepted the server rules.")
        else:
            accepted = await self.bot.db.column("SELECT UserID FROM accepted WHERE GuildID = ?", ctx.guild.id)
            await ctx.send(
                f"{self.bot.info} {len(accepted):,} / {len([m for m in ctx.guild.members if not m.bot]):,} members have accepted the server rules."
            )

    @commands.command(
        name="resetaccepted",
        cooldown_after_parsing=True,
        help="Resets Solaris' records regarding who has accepted the rules in your server. This action is irreversible.",
    )
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @checks.module_has_initialised(MODULE_NAME)
    @checks.module_is_active(MODULE_NAME)
    @checks.author_can_configure()
    async def resetaccepted_command(self, ctx):
        await ctx.bot.db.execute("DELETE FROM accepted WHERE GuildID = ?", ctx.guild.id)
        await ctx.send(f"{self.bot.tick} Acceptance records for this server have been reset.")


def setup(bot):
    bot.add_cog(Gateway(bot))
