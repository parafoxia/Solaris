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
from os import name
from platform import python_version
from time import time

import discord
import psutil
from discord.ext import commands

from solaris.utils import (
    INFO_ICON,
    LOADING_ICON,
    SUCCESS_ICON,
    SUPPORT_GUILD_INVITE_LINK,
    checks,
    chron,
    converters,
    menu,
    string,
)
from solaris.utils.modules import deactivate


class DetailedServerInfoMenu(menu.MultiPageMenu):
    def __init__(self, ctx, table):
        pagemaps = []
        base_pm = {
            "header": "Information",
            "title": f"Detailed server information for {ctx.guild.name}",
            "thumbnail": ctx.guild.icon_url,
        }

        for key, value in table.items():
            pm = base_pm.copy()
            pm.update({"description": f"Showing {key} information.", "fields": value})
            pagemaps.append(pm)

        super().__init__(ctx, pagemaps, timeout=120.0)


class LeavingMenu(menu.SelectionMenu):
    def __init__(self, ctx):
        pagemap = {
            "header": "Leave Wizard",
            "title": "Leaving already?",
            "description": (
                "If you remove Solaris from your server, all server information Solaris has stored, as well as any roles and channels Solaris has created, will be deleted."
                f"If you are having issues with Solaris, consider joining the support server to try and find a resolution - select {ctx.bot.info} to get an invite link.\n\n"
                "Are you sure you want to remove Solaris from your server?"
            ),
            "thumbnail": ctx.bot.user.avatar_url,
        }
        super().__init__(ctx, ["confirm", "cancel", "info"], pagemap, timeout=120.0)

    async def start(self):
        r = await super().start()

        if r == "confirm":
            pagemap = {
                "header": "Leave Wizard",
                "description": "Please wait... This should only take a few seconds.",
                "thumbnail": LOADING_ICON,
            }
            await self.switch(pagemap, clear_reactions=True)
            await self.leave()
        elif r == "cancel":
            await self.stop()
        elif r == "info":
            pagemap = {
                "header": "Leave Wizard",
                "title": "Let's get to the bottom of this!",
                "description": f"Click [here]({SUPPORT_GUILD_INVITE_LINK}) to join the support server.",
                "thumbnail": INFO_ICON,
            }
            await self.switch(pagemap, clear_reactions=True)

    async def leave(self):
        dlc_id, dar_id = (
            await self.bot.db.record(
                "SELECT DefaultLogChannelID, DefaultAdminRoleID FROM system WHERE GuildID = ?", self.ctx.guild.id
            )
            or [None] * 2
        )

        await deactivate.everything(self.ctx)

        if self.ctx.guild.me.guild_permissions.manage_roles and (dar := self.ctx.guild.get_role(dar_id)) is not None:
            await dar.delete(reason="Solaris is leaving the server.")

        if (
            self.ctx.guild.me.guild_permissions.manage_channels
            and (dlc := self.ctx.guild.get_channel(dlc_id)) is not None
        ):
            await dlc.delete(reason="Solaris is leaving the server.")

        pagemap = {
            "header": "Leave Wizard",
            "title": "Sorry to see you go!",
            "description": (
                f"If you ever wish to reinvite Solaris, you can do so by clicking [here]({self.bot.admin_invite}) (recommended permissions), or [here]({self.bot.non_admin_invite}) (minimum required permissions).\n\n"
                "The Solaris team wish you and your server all the best."
            ),
        }
        await self.switch(pagemap)
        await self.ctx.guild.leave()


class Meta(commands.Cog):
    """Commands for retrieving information regarding Solaris, from invitation links to detailed bot statistics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.developer = (await self.bot.application_info()).owner
            self.artist = await self.bot.grab_user(167803836839231488)
            self.testers = [
                (await self.bot.grab_user(id_))
                for id_ in (
                    116520426401693704,
                    300346872109989898,
                    135372594953060352,
                    287969892689379331,
                    254245982395564032,
                )
            ]
            self.support_guild = self.bot.get_guild(661973136631398412)
            self.helper_role = self.support_guild.get_role(689788551575109648)

            self.bot.ready.up(self)

    @commands.command(
        name="about",
        aliases=["credits"],
        help="View information regarding those behind Solaris' development. This includes the developer and the testers, and also shows copyright information.",
    )
    async def about_command(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                title="About Solaris",
                description=f"Use `{prefix}botinfo` for detailed statistics.",
                thumbnail=self.bot.user.avatar_url,
                fields=(
                    ("Developer", self.developer.mention, False),
                    ("Avatar Designer", self.artist.mention, False),
                    ("Testers", string.list_of([t.mention for t in self.testers]), False),
                ),
            )
        )

    @commands.command(name="support", aliases=["sos"], help="Provides an invite link to Solaris' support server.")
    async def support_command(self, ctx):
        online = [m for m in self.support_guild.members if not m.bot and m.status == discord.Status.online]
        helpers = [
            m for m in self.support_guild.members if not m.bot and m.top_role.position >= self.helper_role.position
        ]
        online_helpers = set(online) & set(helpers)

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                description=f"Click [here]({SUPPORT_GUILD_INVITE_LINK}) to join the support server.",
                thumbnail=self.bot.user.avatar_url,
                fields=(
                    ("Online / members", f"{len(online):,} / {len(self.support_guild.members):,}", True),
                    ("Online / helpers", f"{len(online_helpers):,} / {len(helpers):,}", True),
                    ("Developer", str(self.support_guild.owner.status).title(), True),
                ),
            )
        )

    @commands.command(
        name="invite", aliases=["join"], help="Provides the links necessary to invite Solaris to other servers."
    )
    async def invite_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                thumbnail=self.bot.user.avatar_url,
                fields=(
                    (
                        "Primary link",
                        f"To invite Solaris with administrator privileges, click [here]({self.bot.admin_invite}).",
                        False,
                    ),
                    (
                        "Secondary",
                        f"To invite Solaris without administrator privileges, click [here]({self.bot.non_admin_invite}) (you may need to grant Solaris some extra permissions in order to use some modules).",
                        False,
                    ),
                    ("Servers", f"{self.bot.guild_count:,}", True),
                    ("Users", f"{self.bot.user_count:,}", True),
                    ("Get started", "`>>setup`", True),
                ),
            )
        )

    @commands.command(name="source", aliases=["src"], help="Provides a link to Solaris' source code.")
    async def source_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                thumbnail=self.bot.user.avatar_url,
                fields=(
                    (
                        "Available under the GPLv3 license",
                        "Click [here](https://github.com/parafoxia/Solaris) to view.",
                        False,
                    ),
                ),
            )
        )

    @commands.command(
        name="issue",
        aliases=["bugreport", "reportbug", "featurerequest", "requestfeature"],
        help="Provides a link to open an issue on the Solaris repo.",
    )
    async def issue_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                description="If you have discovered a bug not already known or want a feature not requested, open an issue using the green button in the top right of the window.",
                thumbnail=self.bot.user.avatar_url,
                fields=(
                    (
                        "View all known bugs",
                        "Click [here](https://github.com/parafoxia/Solaris/issues?q=is%3Aissue+is%3Aopen+label%3Abug).",
                        False,
                    ),
                    (
                        "View all planned features",
                        "Click [here](https://github.com/parafoxia/Solaris/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement).",
                        False,
                    ),
                ),
            )
        )

    @commands.command(
        name="changelog",
        aliases=["release"],
        help="Provides a link to view the changelog for the given version. If no version is provided, a general overview is provided.",
    )
    async def changelog_command(self, ctx, version: t.Optional[str]):
        url = (
            "https://github.com/parafoxia/Solaris/releases"
            if not version
            else f"https://github.com/parafoxia/Solaris/releases/tag/v{version}"
        )
        version_info = f"version {version}" if version else "all versions"
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                description=f"Click [here]({url}) to information on {version_info}.",
                thumbnail=self.bot.user.avatar_url,
            )
        )

    @commands.command(name="ping", help="Pings Solaris.")
    async def ping_command(self, ctx):
        lat = self.bot.latency * 1000
        s = time()
        pm = await ctx.send(f"{self.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: - ms.")
        e = time()
        await pm.edit(
            content=f"{self.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: {(e-s)*1000:,.0f} ms."
        )

    @commands.command(
        name="botinfo",
        aliases=["bi", "botstats", "stats", "bs"],
        cooldown_after_parsing=True,
        help="Displays statistical information on Solaris. This includes process and composition information, and also includes information about Solaris' reach.",
    )
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def botinfo_command(self, ctx):
        with (proc := psutil.Process()).oneshot():
            prefix = await self.bot.prefix(ctx.guild)
            uptime = time() - proc.create_time()
            cpu_times = proc.cpu_times()
            total_memory = psutil.virtual_memory().total / (1024 ** 2)
            memory_percent = proc.memory_percent()
            memory_usage = total_memory * (memory_percent / 100)

            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title="Bot information",
                    description=f"Solaris was developed by {(await self.bot.application_info()).owner.mention}. Use `{prefix}about` for more information.",
                    thumbnail=self.bot.user.avatar_url,
                    fields=(
                        ("Bot version", f"{self.bot.version}", True),
                        ("Python version", f"{python_version()}", True),
                        ("discord.py version", f"{discord.__version__}", True),
                        ("Uptime", chron.short_delta(dt.timedelta(seconds=uptime)), True),
                        (
                            "CPU time",
                            chron.short_delta(
                                dt.timedelta(seconds=cpu_times.system + cpu_times.user), milliseconds=True
                            ),
                            True,
                        ),
                        (
                            "Memory usage",
                            f"{memory_usage:,.3f} / {total_memory:,.0f} MiB ({memory_percent:.0f}%)",
                            True,
                        ),
                        ("Servers", f"{self.bot.guild_count:,}", True),
                        ("Users", f"{self.bot.user_count:,}", True),
                        ("Commands", f"{self.bot.command_count:,}", True),
                        ("Code", f"{self.bot.loc.code:,} lines", True),
                        ("Comments", f"{self.bot.loc.docs:,} lines", True),
                        ("Blank", f"{self.bot.loc.empty:,} lines", True),
                        (
                            "Database calls since uptime",
                            f"{self.bot.db._calls:,} ({self.bot.db._calls/uptime:,.3f} per second)",
                            True,
                        ),
                    ),
                )
            )

    @commands.command(
        name="userinfo",
        aliases=["ui"],
        help="Displays information on a given user. If no user is provided, Solaris will display your information. Note that although Solaris can display information about any user on Discord, the amount of information available is significantly lower for users not in the server the command was invoked in.",
    )
    async def userinfo_command(
        self, ctx, *, target: t.Optional[t.Union[discord.Member, converters.User, converters.SearchedMember, str]]
    ):
        target = target or ctx.author

        if isinstance(target, discord.Member):
            ps = target.premium_since
            ngr = len(target.guild.roles)

            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"User information for {target.name}",
                    description=(
                        f"This member is also known as {target.display_name} in this server."
                        if target.nick
                        else f"This member does not have a nickname in this server."
                    ),
                    colour=target.colour,
                    thumbnail=target.avatar_url,
                    fields=(
                        ("ID", target.id, False),
                        ("Discriminator", target.discriminator, True),
                        ("Bot?", target.bot, True),
                        ("Admin?", target.guild_permissions.administrator, True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Joined on", chron.long_date(target.joined_at), True),
                        ("Boosted on", chron.long_date(ps) if ps else "-", True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                        ("Member for", chron.short_delta(dt.datetime.utcnow() - target.joined_at), True),
                        ("Booster for", chron.short_delta(dt.datetime.utcnow() - ps) if ps else "-", True),
                        ("Status", str(target.status).title(), True),
                        (
                            "Activity type",
                            str(target.activity.type).title().split(".")[-1] if target.activity is not None else "-",
                            True,
                        ),
                        ("Activity name", target.activity.name if target.activity else "-", True),
                        ("Nº of roles", f"{len(target.roles)-1:,}", True),
                        ("Top role", target.top_role.mention, True),
                        ("Top role position", f"{string.ordinal(ngr - target.top_role.position)} / {ngr:,}", True),
                    ),
                )
            )

        elif isinstance(target, discord.User):
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"User information for {target.name}",
                    description="Showing reduced information as the given user is not in this server.",
                    thumbnail=target.avatar_url,
                    fields=(
                        ("ID", target.id, True),
                        ("Discriminator", target.discriminator, True),
                        ("Bot?", target.bot, True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                        ("\u200b", "\u200b", True),
                    ),
                )
            )

        else:
            await ctx.send(f"{self.bot.cross} Solaris was unable to identify a user with the information provided.")

    @commands.command(
        name="serverinfo", aliases=["si", "guildinfo", "gi"], help="Displays information on your server."
    )
    async def serverinfo_command(self, ctx):
        bot_count = len([m for m in ctx.guild.members if m.bot])
        human_count = ctx.guild.member_count - bot_count

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Server information for {ctx.guild.name}",
                thumbnail=ctx.guild.icon_url,
                colour=ctx.guild.owner.colour,
                fields=(
                    ("ID", ctx.guild.id, False),
                    ("Owner", ctx.guild.owner.mention, True),
                    ("Region", ctx.guild.region, True),
                    ("Top role", ctx.guild.roles[-1].mention, True),
                    ("Members", f"{ctx.guild.member_count:,}", True),
                    ("Humans / bots", f"{human_count:,} / {bot_count:,}", True),
                    (
                        "Bans",
                        f"{len(await ctx.guild.bans()):,}" if ctx.guild.me.guild_permissions.ban_members else "-",
                        True,
                    ),
                    ("Roles", f"{len(ctx.guild.roles)-1:,}", True),
                    ("Text channels", f"{len(ctx.guild.text_channels):,}", True),
                    ("Voice channels", f"{len(ctx.guild.voice_channels):,}", True),
                    (
                        "Invites",
                        f"{len(await ctx.guild.invites()):,}" if ctx.guild.me.guild_permissions.manage_guild else "-",
                        True,
                    ),
                    ("Emojis", f"{len(ctx.guild.emojis):,} / {ctx.guild.emoji_limit*2:,}", True),
                    ("Boosts", f"{ctx.guild.premium_subscription_count:,} (level {ctx.guild.premium_tier})", True),
                    ("Newest member", max(ctx.guild.members, key=lambda m: m.joined_at).mention, True),
                    ("Created on", chron.long_date(ctx.guild.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - ctx.guild.created_at), True),
                    (
                        "Statuses",
                        (
                            f"🟢 {len([m for m in ctx.guild.members if m.status == discord.Status.online]):,} "
                            f"🟠 {len([m for m in ctx.guild.members if m.status == discord.Status.idle]):,} "
                            f"🔴 {len([m for m in ctx.guild.members if m.status == discord.Status.dnd]):,} "
                            f"⚪ {len([m for m in ctx.guild.members if m.status == discord.Status.offline]):,}"
                        ),
                        False,
                    ),
                ),
            )
        )

    @commands.command(
        name="channelinfo",
        aliases=["categoryinfo", "ci"],
        help="Displays information on a given channel or category. If no channel or category is provided, Solaris will display information on the channel the command was invoked in.",
    )
    async def channelinfo_command(
        self,
        ctx,
        *,
        target: t.Optional[t.Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, str]],
    ):
        target = target or ctx.channel

        if isinstance(target, discord.TextChannel):
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"Channel information for {target.name}",
                    description="This channel is a text channel.",
                    thumbnail=ctx.guild.icon_url,
                    fields=(
                        ("ID", target.id, False),
                        ("NSFW?", target.is_nsfw(), True),
                        ("News?", target.is_news(), True),
                        ("Synced?", target.permissions_synced, True),
                        ("Category", target.category.name, True),
                        ("Position", f"{string.ordinal(target.position+1)} / {len(ctx.guild.text_channels):,}", True),
                        ("Allowed members", f"{len(target.members):,}", True),
                        ("Overwrites", f"{len(target.overwrites)}", True),
                        (
                            "Invites",
                            f"{len(await target.invites()):,}" if ctx.guild.me.guild_permissions.manage_guild else "-",
                            True,
                        ),
                        ("Pins", f"{len(await target.pins())}", True),
                        ("Slowmode delay", f"{target.slowmode_delay:,} second(s)", True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                        ("Topic", target.topic or "This channel does not have a topic.", False),
                    ),
                )
            )

        elif isinstance(target, discord.VoiceChannel):
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"Channel information for {target.name}",
                    description="This channel is a voice channel.",
                    thumbnail=ctx.guild.icon_url,
                    fields=(
                        ("ID", target.id, False),
                        ("Synced?", target.permissions_synced, True),
                        ("Category", target.category.name, True),
                        ("Bitrate", f"{target.bitrate//1000:,.0f} kbps", True),
                        ("Position", f"{string.ordinal(target.position+1)} / {len(ctx.guild.voice_channels):,}", True),
                        ("Overwrites", f"{len(target.overwrites)}", True),
                        (
                            "Invites",
                            f"{len(await target.invites()):,}" if ctx.guild.me.guild_permissions.manage_guild else "-",
                            True,
                        ),
                        ("Members joined", f"{len(target.members):,} / {target.user_limit or '∞'}", True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                    ),
                )
            )

        elif isinstance(target, discord.CategoryChannel):
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"Category information for {target.name}",
                    thumbnail=ctx.guild.icon_url,
                    fields=(
                        ("ID", target.id, False),
                        ("NSFW?", target.is_nsfw(), True),
                        ("Synced?", target.permissions_synced, True),
                        ("Position", f"{string.ordinal(target.position+1)} / {len(ctx.guild.categories):,}", True),
                        ("Channels", f"{len(target.channels):,} / {len(ctx.guild.channels):,}", True),
                        ("Text / voice", f"{len(target.text_channels):,} / {len(target.voice_channels):,}", True),
                        ("Synced channels", f"{len([c for c in target.channels if c.permissions_synced])}", True),
                        ("Overwrites", f"{len(target.overwrites)}", True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                    ),
                )
            )

        else:
            await ctx.send(f"{self.bot.cross} Solaris was unable to identify a channel with the information provided.")

    @commands.command(
        name="roleinfo",
        aliases=["ri"],
        help="Displays information on a given role. If no role is provided, Solaris will display information on your top role.",
    )
    async def roleinfo_command(self, ctx, *, target: t.Optional[t.Union[discord.Role, str]]):
        target = target or ctx.author.top_role

        if isinstance(target, discord.Role):
            ngr = len(ctx.guild.roles)

            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"Role information for {target.name}",
                    description=f"You currently{' ' if target in ctx.author.roles else ' do not '}have this role.",
                    thumbnail=ctx.guild.icon_url,
                    colour=target.colour,
                    fields=(
                        ("ID", target.id, False),
                        ("Hoisted?", target.hoist, True),
                        ("Assignable?", not target.managed, True),
                        ("Mentionable?", target.mentionable, True),
                        ("Admin?", target.permissions.administrator, True),
                        ("Position", f"{string.ordinal(ngr - target.position)} / {ngr:,}", True),
                        ("Colour", f"#{str(target.colour)}", True),
                        ("Members", f"{len(target.members):,}", True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                    ),
                )
            )

        else:
            await ctx.send(f"{self.bot.cross} Solaris was unable to identify a role with the information provided.")

    @commands.command(
        name="messageinfo",
        aliases=["mi"],
        help='Displays information on a given message. Hint: If you are in developer mode, you can hold SHIFT while clicking on the "Copy ID" option to get a channelid-messageid format. This allows you to get information for messages in different channels.',
    )
    async def messageinfo_command(self, ctx, target: t.Union[discord.Message, str]):
        if isinstance(target, discord.Message):
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"Message information",
                    description=f"You can see the original message [here]({target.jump_url}).",
                    thumbnail=target.author.avatar_url,
                    colour=target.author.colour,
                    fields=(
                        ("ID", target.id, False),
                        ("System?", target.is_system(), True),
                        ("Embedded?", bool(target.embeds), True),
                        ("Pinned?", target.pinned, True),
                        ("Author", target.author.mention, True),
                        ("Channel", target.channel.mention, True),
                        ("Reactions", f"{len(target.reactions):,}", True),
                        ("Member mentions", f"{len(target.mentions):,}", True),
                        ("Role mentions", f"{len(target.role_mentions):,}", True),
                        ("Attachments", f"{len(target.attachments):,}", True),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                        ("Last edited on", chron.long_date(target.created_at), True),
                        (
                            "Content",
                            target.content if len(target.content) <= 1024 else f"{target.content[:1021]}...",
                            False,
                        ),
                    ),
                )
            )

        else:
            await ctx.send(f"{self.bot.cross} Solaris was unable to identify a message with the information provided.")

    @commands.command(
        name="emojiinfo",
        aliases=["ei"],
        help="Displays information on a given emoji. This only works for custom emoji.",
    )
    async def emojiinfo_command(self, ctx, target: t.Union[discord.Emoji, str]):
        if isinstance(target, discord.Emoji):
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    title=f"Emoji information for {target.name}",
                    thumbnail=target.url,
                    fields=(
                        ("ID", target.id, False),
                        ("Animated?", target.animated, True),
                        ("Managed?", target.managed, True),
                        ("Available?", target.available, True),
                        (
                            "Created by",
                            u.mention if (u := target.user) and ctx.guild.me.guild_permissions.manage_emojis else "-",
                            True,
                        ),
                        ("Created on", chron.long_date(target.created_at), True),
                        ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True),
                    ),
                )
            )

        else:
            await ctx.send(
                f"{self.bot.cross} Solaris was unable to identify an emoji with the information provided. Are you sure it is a custom emoji?"
            )

    @commands.command(
        name="detailedserverinfo",
        aliases=["dsi", "detailedguildinfo", "dgi"],
        cooldown_after_parsing=True,
        help="Displays more detailed information on your server. This command does not display well on smaller displays.",
    )
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def detailedserverinfo_command(self, ctx):
        table = {
            "overview": (
                ("ID", ctx.guild.id, False),
                ("Name", ctx.guild.name, True),
                ("Region", ctx.guild.region, True),
                ("Inactive channel", ctx.guild.afk_channel, True),
                ("Inactive timeout", f"{ctx.guild.afk_timeout//60:,} mins", True),
                ("System messages channel", ctx.guild.system_channel.mention, True),
                ("Send welcome messages?", ctx.guild.system_channel_flags.join_notifications, True),
                ("Send boost messages?", ctx.guild.system_channel_flags.premium_subscriptions, True),
                (
                    "Default notifications",
                    "Only @mentions" if ctx.guild.default_notifications.value else "All Messages",
                    True,
                ),
                ("\u200b", "\u200b", True),
            ),
            "moderation": (
                ("Verficiation level", str(ctx.guild.verification_level).title(), False),
                (
                    "Explicit media content filter",
                    str(ctx.guild.explicit_content_filter).replace("_", " ").title(),
                    False,
                ),
                ("2FA requirement for moderation?", bool(ctx.guild.mfa_level), False),
            ),
            "numerical": (
                ("Members", f"{ctx.guild.member_count:,}", True),
                ("Humans", f"{(hc := len([m for m in ctx.guild.members if not m.bot])):,}", True),
                ("Bots", f"{ctx.guild.member_count - hc:,}", True),
                ("Est. prune (1d)", f"{await ctx.guild.estimate_pruned_members(days=1):,}", True),
                ("Est. prune (7d)", f"{await ctx.guild.estimate_pruned_members(days=7):,}", True),
                ("Est. prune (30d)", f"{await ctx.guild.estimate_pruned_members(days=30):,}", True),
                ("Roles", f"{len(ctx.guild.roles):,}", True),
                (
                    "Members with top role",
                    f"{len([m for m in ctx.guild.members if ctx.guild.roles[-1] in m.roles]):,}",
                    True,
                ),
                (
                    "Bans",
                    f"{len(await ctx.guild.bans()) if ctx.guild.me.guild_permissions.ban_members else None:,}",
                    True,
                ),
                (
                    "Invites",
                    f"{len(await ctx.guild.invites()) if ctx.guild.me.guild_permissions.manage_guild else None:,}",
                    True,
                ),
                (
                    "Webhooks",
                    f"{len(await ctx.guild.webhooks()) if ctx.guild.me.guild_permissions.manage_webhooks else None:,}",
                    True,
                ),
                ("Emojis", f"{len(ctx.guild.emojis):,}", True),
                ("Bitrate limit", f"{ctx.guild.bitrate_limit//1000:,.0f} kbps", True),
                ("Filesize limit", f"{ctx.guild.filesize_limit//(1024**2):,.0f} MB", True),
                ("Boosts", f"{ctx.guild.premium_subscription_count:,}", True),
                ("Boosters", f"{len(ctx.guild.premium_subscribers):,}", True),
                ("\u200b", "\u200b", True),
                ("\u200b", "\u200b", True),
            ),
            # "miscellaneous": [
            # ]
        }

        await DetailedServerInfoMenu(ctx, table).start()

    @commands.command(
        name="avatar",
        aliases=["profile", "pfp"],
        help="Displays the avatar (profile picture) of a given user. This is not limited to server members.",
    )
    async def avatar_command(
        self, ctx, *, target: t.Optional[t.Union[discord.Member, converters.User, converters.SearchedMember, str]]
    ):
        target = target or ctx.author

        if isinstance(target, discord.Member) or isinstance(target, discord.User):
            name = getattr(target, "display_name", target.name)
            await ctx.send(
                embed=self.bot.embed.build(
                    ctx=ctx,
                    header="Information",
                    description=f"Displaying avatar for {name}.",
                    image=target.avatar_url,
                )
            )
        else:
            await ctx.send(f"{self.bot.cross} Solaris was unable to identify a user with the information provided.")

    @commands.command(name="icon", help="Displays the icon of your server.")
    async def icon_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                description=f"Displaying icon for {ctx.guild.name}.",
                image=ctx.guild.icon_url,
            )
        )

    @commands.command(
        name="leave",
        help="Utility to make Solaris clean up before leaving the server. This involves deactivating all active modules and deleting the default log channel and the default admin role should they still exist.",
    )
    @checks.author_can_configure()
    async def leave_command(self, ctx):
        await LeavingMenu(ctx).start()

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown_command(self, ctx):
        # Use hub shutdown instead where possible.
        await ctx.message.delete()
        await self.bot.shutdown()


def setup(bot):
    bot.add_cog(Meta(bot))
