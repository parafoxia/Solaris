import datetime as dt
import typing as t
from os import name
from platform import python_version
from time import time

import discord
import psutil
from beautifultable import BeautifulTable
from discord.ext import commands

from s4.utils import chron, converters, string, menu


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
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="about", aliases=["credits"])
    async def about_command(self, ctx):
        self.developer = (await self.bot.application_info()).owner.mention
        self.testers = "\n".join(
            [
                (await self.bot.grab_user(id_)).mention
                for id_ in (116520426401693704, 300346872109989898, 135372594953060352)
            ]
        )

        await ctx.send(embed=self.bot.embed.load("about bot", ctx=ctx, thumbnail=self.bot.user.avatar_url, info=self))

    @commands.command(name="support", aliases=["sos"])
    async def support_command(self, ctx):
        sg = self.bot.get_guild(661973136631398412)
        hr = sg.get_role(689788551575109648)

        await ctx.send(
            embed=self.bot.embed.load(
                "support link",
                ctx=ctx,
                online_m=len([m for m in sg.members if m.status == discord.Status.online]),
                members=len(sg.members),
                online_h=len(
                    [m for m in sg.members if m.top_role.position >= hr.position and str(m.status) == "online"]
                )
                - 1,
                helpers=len([m for m in sg.members if m.top_role.position >= hr.position]) - 1,
                status=str(sg.owner.status).title(),
            )
        )

    @commands.command(name="invite", aliases=["join"])
    async def invite_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.load(
                "invite link", ctx=ctx, al=self.bot.admin_invite, nal=self.bot.non_admin_invite, bot=self.bot
            )
        )

    @commands.command(name="ping")
    async def ping_command(self, ctx):
        lat = self.bot.latency * 1000
        s = time()
        pm = await ctx.send(f"{self.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: - ms.")
        e = time()
        await pm.edit(
            content=f"{self.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: {(e-s)*1000:,.0f} ms."
        )

    @commands.command(name="prefix")
    async def prefix_command(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        await ctx.send(
            f"{self.bot.info} S4's prefix in this server is {prefix}. To change it, use `{prefix}config system prefix <new prefix>`."
        )

    @commands.command(name="botinfo", aliases=["bi", "botstats", "stats", "bs"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def botinfo_command(self, ctx):
        with (proc := psutil.Process()).oneshot():
            await ctx.send(
                embed=self.bot.embed.load(
                    "bot info",
                    ctx=ctx,
                    thumbnail=self.bot.user.avatar_url,
                    bot=self.bot,
                    owner=(await self.bot.application_info()).owner,
                    py_version=python_version(),
                    dpy_version=discord.__version__,
                    uptime=chron.short_delta(dt.timedelta(seconds=(secs := time() - proc.create_time()))),
                    cpu_time=chron.short_delta(dt.timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user)),
                    mem_total=(mt := psutil.virtual_memory().total / (1024 ** 2)),
                    mem_percent=(mp := proc.memory_percent()),
                    mem_usage=mt * (mp / 100),
                    json_lines=0,
                    sql_lines=0,
                    db_calls=self.bot.db._calls,
                    db_calls_ps=self.bot.db._calls / secs,
                )
            )

    @commands.command(name="userinfo", aliases=["ui", "memberinfo", "mi"])
    async def userinfo_command(
        self, ctx, *, target: t.Optional[t.Union[discord.Member, converters.User, converters.SearchedMember, str]]
    ):
        target = target or ctx.author

        if isinstance(target, discord.Member):
            await ctx.send(
                embed=self.bot.embed.load(
                    "member info",
                    ctx=ctx,
                    description=f"This member is also known as {target.display_name} in this server."
                    if target.nick
                    else "This member does not have a nickname in this server.",
                    thumbnail=target.avatar_url,
                    target=target,
                    created_on=chron.long_date(target.created_at),
                    joined_on=chron.long_date(target.joined_at),
                    boosted_on=chron.long_date(ps) if (ps := target.premium_since) else "-",
                    existed_for=chron.short_delta(dt.datetime.utcnow() - target.created_at),
                    member_for=chron.short_delta(dt.datetime.utcnow() - target.joined_at),
                    booster_for=chron.short_delta(dt.datetime.utcnow() - ps) if ps else "-",
                    status=str(target.status).title(),
                    activity_type=str(target.activity.type).title().split(".")[-1]
                    if target.activity is not None
                    else "-",
                    activity_name=target.activity.name if target.activity else "-",
                    no_of_roles=len(target.roles),
                    no_of_guild_roles=(ngr := len(target.guild.roles)),
                    top_role_position=string.ordinal(ngr - target.top_role.position),
                )
            )

        elif isinstance(target, discord.User):
            await ctx.send(
                embed=self.bot.embed.load(
                    "user info",
                    ctx=ctx,
                    thumbnail=target.avatar_url,
                    target=target,
                    created_on=chron.long_date(target.created_at),
                    existed_for=chron.short_delta(dt.datetime.utcnow() - target.created_at),
                )
            )

        else:
            await ctx.send(f"{self.bot.cross} S4 was unable to identify a user with the information provided.")

    @commands.command(name="avatar", aliases=["profile", "pfp"])
    async def avatar_command(
        self, ctx, *, target: t.Optional[t.Union[discord.Member, converters.User, converters.SearchedMember, str]]
    ):
        target = target or ctx.author

        if isinstance(target, discord.Member) or isinstance(target, discord.User):
            name = getattr(target, "display_name", target.name)
            await ctx.send(embed=self.bot.embed.load("user avatar", ctx=ctx, image=target.avatar_url, name=name))
        else:
            await ctx.send(f"{self.bot.cross} S4 was unable to identify a user with the information provided.")

    @commands.command(name="serverinfo", aliases=["si", "guildinfo", "gi"])
    async def serverinfo_command(self, ctx):
        await ctx.send(
            embed=self.bot.embed.load(
                "guild info",
                ctx=ctx,
                thumbnail=ctx.guild.icon_url,
                target=ctx.guild,
                top_role=ctx.guild.roles[-1],
                bot_count=(bc := len([m for m in ctx.guild.members if m.bot])),
                human_count=ctx.guild.member_count - bc,
                ban_count=f"{len(await ctx.guild.bans()):,}" if ctx.guild.me.guild_permissions.ban_members else "-",
                role_count=len(ctx.guild.roles),
                tc_count=len(ctx.guild.text_channels),
                vc_count=len(ctx.guild.voice_channels),
                invite_count=f"{len(await ctx.guild.invites()):,}"
                if ctx.guild.me.guild_permissions.manage_guild
                else "-",
                emoji_count=len(ctx.guild.emojis),
                emoji_limit=ctx.guild.emoji_limit,
                newest_member=max(ctx.guild.members, key=lambda m: m.joined_at),
                created_on=chron.long_date(ctx.guild.created_at),
                existed_for=chron.short_delta(dt.datetime.utcnow() - ctx.guild.created_at),
                online_count=len([m for m in ctx.guild.members if m.status == discord.Status.online]),
                idle_count=len([m for m in ctx.guild.members if m.status == discord.Status.idle]),
                dnd_count=len([m for m in ctx.guild.members if m.status == discord.Status.dnd]),
                offline_count=len([m for m in ctx.guild.members if m.status == discord.Status.offline]),
            )
        )

    @commands.command(name="detailedserverinfo", aliases=["dsi", "detailedguildinfo", "dgi"])
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

    @commands.command(name="icon")
    async def icon_command(self, ctx):
        await ctx.send(embed=self.bot.embed.load("guild icon", ctx=ctx, image=ctx.guild.icon_url, target=ctx.guild))

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
