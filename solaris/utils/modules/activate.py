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

from solaris.utils.modules import retrieve


async def gateway(ctx):
    async with ctx.typing():
        active, rc_id, br_id, gt = (
            await ctx.bot.db.record(
                "SELECT Active, RulesChannelID, BlockingRoleID, GateText FROM gateway WHERE GuildID = ?", ctx.guild.id
            )
            or [None] * 4
        )

        if active:
            await ctx.send(f"{ctx.bot.cross} The gateway module is already active.")
        elif not (ctx.guild.me.guild_permissions.manage_roles and ctx.guild.me.guild_permissions.kick_members):
            await ctx.send(
                f"{ctx.bot.cross} The gateway module could not be activated as Solaris does not have the Manage Roles and Kick Members permissions."
            )
        elif (rc := ctx.bot.get_channel(rc_id)) is None:
            await ctx.send(
                f"{ctx.bot.cross} The gateway module could not be activated as the rules channel does not exist or can not be accessed by Solaris."
            )
        elif ctx.guild.get_role(br_id) is None:
            await ctx.send(
                f"{ctx.bot.cross} The gateway module could not be activated as the blocking role does not exist or can not be accessed by Solaris."
            )
        else:
            gm = await rc.send(
                gt
                or f"**Attention:** Do you accept the rules outlined above? If you do, select {ctx.bot.emoji.mention('confirm')}, otherwise select {ctx.bot.emoji.mention('cancel')}."
            )
            for emoji in ctx.bot.emoji.get_many("confirm", "cancel"):
                await gm.add_reaction(emoji)

            await ctx.bot.db.execute(
                "UPDATE gateway SET Active = 1, GateMessageID = ? WHERE GuildID = ?", gm.id, ctx.guild.id
            )
            await ctx.send(f"{ctx.bot.tick} The gateway module has been activated.")
            lc = await retrieve.log_channel(ctx.bot, ctx.guild)
            await lc.send(f"{ctx.bot.info} The gateway module has been activated.")
