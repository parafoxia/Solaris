# S4 - A security and statistics focussed Discord bot.
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
from beautifultable import BeautifulTable
from discord.ext import commands

from s4.utils import SUPPORT_GUILD_INVITE_LINK, chron, converters, menu, string


class DetailedServerInfoMenu(menu.MultiPageMenu):
    def __init__(self, ctx, table_info):
        pagemaps = []
        base_pm = {
            "header": "Information",
            "title": f"Server information for {ctx.guild.name}",
            "thumbnail": ctx.guild.icon_url,
        }

        for infotype, rows in table_info.items():
            table = BeautifulTable()
            table.set_style(BeautifulTable.STYLE_BOX_ROUNDED)

            for row in rows:
                table.rows.append(row)

            pm = base_pm.copy()
            pm.update(description=f"Showing {infotype} information.\n```{table}```")
            pagemaps.append(pm)

        super().__init__(ctx, pagemaps, timeout=120.0)


class Meta(commands.Cog):
    """Commands for retrieving information regarding S4, from invitation links to detailed bot statistics."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.developer = (await self.bot.application_info()).owner
            self.testers = [
                (await self.bot.grab_user(id_)) for id_ in (116520426401693704, 300346872109989898, 135372594953060352)
            ]
            self.support_guild = self.bot.get_guild(661973136631398412)
            self.helper_role = self.support_guild.get_role(689788551575109648)

            self.bot.ready.up(self)

    @commands.command(
        name="about",
        aliases=["credits"],
        help="View information regarding those behind S4's development. This includes the developer and the testers, and also shows copyright information.",
    )
    async def about_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                title="About S4",
                description="Use `botinfo` for detailed statistics.",
                thumbnail=self.bot.user.avatar_url,
                fields=[
                    ["Developer", f"Created and copyright ©️ {self.developer.mention} 2020.", False],
                    ["Testers", "\n".join(t.mention for t in self.testers), False],
                ],
            )
        )

    @commands.command(name="support", aliases=["sos"], help="Provides an invite link to S4's support server.")
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
                fields=[
                    ["Online / members", f"{len(online):,} / {len(self.support_guild.members):,}", True],
                    ["Online / helpers", f"{len(online_helpers):,} / {len(helpers):,}", True],
                    ["Developer", str(self.support_guild.owner.status).title(), True],
                ],
            )
        )

    @commands.command(
        name="invite", aliases=["join"], help="Provides the links necessary to invite S4 to other servers."
    )
    async def invite_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Information",
                thumbnail=self.bot.user.avatar_url,
                fields=[
                    [
                        "Link 1",
                        f"To invite S4 with the Administrator permission, click [here]({self.bot.admin_invite}).",
                        False,
                    ],
                    [
                        "Link 2",
                        f"To invite S4 with the minimum required permissions, click [here]({self.bot.non_admin_invite}) (you may need to grant S4 some extra permissions in order to use some modules).",
                        False,
                    ],
                    ["Servers", f"{self.bot.guild_count:,}", True],
                    ["Users", f"{self.bot.user_count:,}", True],
                    ["Get started", "`>>setup`", True],
                ],
            )
        )

    @commands.command(name="ping", help="Pings S4.")
    async def ping_command(self, ctx):
        lat = self.bot.latency * 1000
        s = time()
        pm = await ctx.send(f"{self.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: - ms.")
        e = time()
        await pm.edit(
            content=f"{self.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: {(e-s)*1000:,.0f} ms."
        )

    @commands.command(
        name="prefix", help="Displays S4's prefix in your server. Note that mentioning S4 will always work."
    )
    async def prefix_command(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        await ctx.send(
            f"{self.bot.info} S4's prefix in this server is {prefix}. To change it, use `{prefix}config system prefix <new prefix>`."
        )

    @commands.command(
        name="botinfo",
        aliases=["bi", "botstats", "stats", "bs"],
        cooldown_after_parsing=True,
        help="Displays statistical information on S4. This includes process and composition information, and also includes information about S4's reach.",
    )
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def botinfo_command(self, ctx):
        with (proc := psutil.Process()).oneshot():
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
                    description=f"S4 was developed by {(await self.bot.application_info()).owner.mention}. Use `about` for more information.",
                    thumbnail=self.bot.user.avatar_url,
                    fields=[
                        ["Bot version", f"{self.bot.version}", True],
                        ["Python version", f"{python_version()}", True],
                        ["discord.py version", f"{discord.__version__}", True],
                        ["Uptime", chron.short_delta(dt.timedelta(seconds=uptime)), True],
                        [
                            "CPU time",
                            chron.short_delta(
                                dt.timedelta(seconds=cpu_times.system + cpu_times.user), milliseconds=True
                            ),
                            True,
                        ],
                        ["Memory usage", f"{memory_usage:,.3f} / {total_memory:,.0f} ({memory_percent:.0f}%)", True],
                        ["Servers", f"{self.bot.guild_count:,}", True],
                        ["Users", f"{self.bot.user_count:,}", True],
                        ["Commands", f"{self.bot.command_count:,}", True],
                        ["Python code", f"{self.bot._python_lines:,} lines", True],
                        ["JSON scripts", f"{self.bot._json_lines:,} lines", True],
                        ["SQL scripts", f"{self.bot._sql_lines:,} lines", True],
                        [
                            "Database calls since uptime",
                            f"{self.bot.db._calls:,} ({self.bot.db._calls/uptime:,.3f} per second)",
                            True,
                        ],
                    ],
                )
            )

    @commands.command(
        name="userinfo",
        aliases=["ui", "memberinfo", "mi"],
        help="Displays information on a given user. If no user is provided, S4 will display your information. Note that although S4 can display information about any user on Discord, the amount of information available is significantly lower for users not in the server the command was invoked in.",
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
                    description=(
                        f"This member is also known as {target.display_name} in this server."
                        if target.nick
                        else "This member does not have a nickname in this server."
                    ),
                    colour=target.colour,
                    thumbnail=target.avatar_url,
                    fields=[
                        ["ID", target.id, False],
                        ["Discriminator", target.discriminator, True],
                        ["Bot?", target.bot, True],
                        ["Admin?", target.guild_permissions.administrator, True],
                        ["Created on", chron.long_date(target.created_at), True],
                        ["Joined on", chron.long_date(target.joined_at), True],
                        ["Boosted on", chron.long_date(ps) if ps else "-", True],
                        ["Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True],
                        ["Member for", chron.short_delta(dt.datetime.utcnow() - target.joined_at), True],
                        ["Booster for", chron.short_delta(dt.datetime.utcnow() - ps) if ps else "-", True],
                        ["Status", str(target.status).title(), True],
                        [
                            "Activity type",
                            str(target.activity.type).title().split(".")[-1] if target.activity is not None else "-",
                            True,
                        ],
                        ["Activity name", target.activity.name if target.activity else "-", True],
                        ["Nº of roles", f"{len(target.roles):,}", True],
                        ["Top role", target.top_role.mention, True],
                        ["Top role position", f"{string.ordinal(ngr - target.top_role.position)} / {ngr:,}", True],
                    ],
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
                    fields=[
                        ["ID", target.id, True],
                        ["Discriminator", target.discriminator, True],
                        ["Bot?", target.bot, True],
                        ["Created on", chron.long_date(target.created_at), True],
                        ["Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at), True],
                        ["\u200b", "\u200b", True],
                    ],
                )
            )

        else:
            await ctx.send(f"{self.bot.cross} S4 was unable to identify a user with the information provided.")

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
            await ctx.send(f"{self.bot.cross} S4 was unable to identify a user with the information provided.")

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
                fields=[
                    ["ID", ctx.guild.id, False],
                    ["Owner", ctx.guild.owner.mention, True],
                    ["Region", ctx.guild.region, True],
                    ["Top role", ctx.guild.roles[-1].mention, True],
                    ["Members", f"{ctx.guild.member_count:,}", True],
                    ["Humans / bots", f"{human_count:,} / {bot_count:,}", True],
                    [
                        "Bans",
                        f"{len(await ctx.guild.bans()):,}" if ctx.guild.me.guild_permissions.ban_members else "-",
                        True,
                    ],
                    ["Roles", f"{len(ctx.guild.roles):,}", True],
                    ["Text channels", f"{len(ctx.guild.text_channels):,}", True],
                    ["Voice channels", f"{len(ctx.guild.voice_channels):,}", True],
                    [
                        "Invites",
                        f"{len(await ctx.guild.invites()):,}" if ctx.guild.me.guild_permissions.manage_guild else "-",
                        True,
                    ],
                    ["Emojis", f"{len(ctx.guild.emojis):,} / {ctx.guild.emoji_limit:,}", True],
                    ["Boosts", f"{ctx.guild.premium_subscription_count:,} (level {ctx.guild.premium_tier})", True],
                    ["Newest member", max(ctx.guild.members, key=lambda m: m.joined_at).mention, True],
                    ["Created on", chron.long_date(ctx.guild.created_at), True],
                    ["Existed for", chron.short_delta(dt.datetime.utcnow() - ctx.guild.created_at), True],
                    [
                        "Statuses",
                        (
                            f"🟢 {len([m for m in ctx.guild.members if m.status == discord.Status.online]):,} "
                            f"🟠 {len([m for m in ctx.guild.members if m.status == discord.Status.idle]):,} "
                            f"🔴 {len([m for m in ctx.guild.members if m.status == discord.Status.dnd]):,} "
                            f"⚪ {len([m for m in ctx.guild.members if m.status == discord.Status.offline]):,}"
                        ),
                        False,
                    ],
                ],
            )
        )

    @commands.command(
        name="detailedserverinfo",
        aliases=["dsi", "detailedguildinfo", "dgi"],
        cooldown_after_parsing=True,
        help="Displays more detailed information on your server. This command does not display well on smaller displays.",
    )
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def detailedserverinfo_command(self, ctx):
        table_info = {
            "overview": [
                ("ID", ctx.guild.id),
                ("Name", ctx.guild.name),
                ("Region", ctx.guild.region),
                ("Inactive channel", ctx.guild.afk_channel),
                ("Inactive timeout", f"{ctx.guild.afk_timeout//60:,} mins"),
                ("System messages channel", ctx.guild.system_channel),
                ("Send welcome messages?", ctx.guild.system_channel_flags.join_notifications),
                ("Send boost messages?", ctx.guild.system_channel_flags.premium_subscriptions),
                (
                    "Default notifications",
                    "Only @mentions" if ctx.guild.default_notifications.value else "All Messages",
                ),
            ],
            "moderation": [
                ("Verficiation level", str(ctx.guild.verification_level).title()),
                ("Explicit media content filter", str(ctx.guild.explicit_content_filter).replace("_", " ").title()),
                ("2FA requirement for moderation", ctx.guild.mfa_level),
            ],
            "numerical": [
                ("Members", f"{ctx.guild.member_count:,}"),
                ("Humans", f"{(hc := len([m for m in ctx.guild.members if not m.bot])):,}"),
                ("Bots", f"{ctx.guild.member_count - hc:,}"),
                ("Est. prune (1d)", f"{await ctx.guild.estimate_pruned_members(days=1):,}"),
                ("Est. prune (7d)", f"{await ctx.guild.estimate_pruned_members(days=7):,}"),
                ("Est. prune (30d)", f"{await ctx.guild.estimate_pruned_members(days=30):,}"),
                ("Roles", f"{len(ctx.guild.roles):,}"),
                (
                    "Members with top role",
                    f"{len([m for m in ctx.guild.members if ctx.guild.roles[-1] in m.roles]):,}",
                ),
                ("Bans", f"{len(await ctx.guild.bans()) if ctx.guild.me.guild_permissions.ban_members else None:,}"),
                (
                    "Invites",
                    f"{len(await ctx.guild.invites()) if ctx.guild.me.guild_permissions.manage_guild else None:,}",
                ),
                (
                    "Webhooks",
                    f"{len(await ctx.guild.webhooks()) if ctx.guild.me.guild_permissions.manage_webhooks else None:,}",
                ),
                ("Emojis", f"{len(ctx.guild.emojis):,}"),
                ("Bitrate limit", f"{ctx.guild.bitrate_limit//1000:,.0f} kbps"),
                ("Filesize limit", f"{ctx.guild.filesize_limit//(1024**2):,.0f} MB"),
                ("Boosts", f"{ctx.guild.premium_subscription_count:,}"),
                ("Boosters", f"{len(ctx.guild.premium_subscribers):,}"),
            ],
            # "miscellaneous": [
            # ]
        }

        await DetailedServerInfoMenu(ctx, table_info).start()

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

    @commands.command(name="leave")
    async def leave_command(self, ctx):
        pass

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown_command(self, ctx):
        # Use hub shutdown instead where possible.
        await self.bot.shutdown()


def setup(bot):
    bot.add_cog(Meta(bot))
