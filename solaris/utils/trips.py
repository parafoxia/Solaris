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

import discord

from solaris.utils.modules import retrieve


async def gateway(okay, reason):
    rc_id, gm_id = (
        await okay.bot.db.record("SELECT RulesChannelID, GateMessageID FROM gateway WHERE GuildID = ?", okay.guild.id,)
        or [None] * 2
    )
    lc = await retrieve.log_channel(okay.bot, okay.guild)

    try:
        if (rc := okay.bot.get_channel(rc_id)) is not None:
            gm = await rc.fetch_message(gm_id)
            await gm.delete()
            await lc.send(f"{okay.bot.info} The gate message was deleted.")
    except (discord.NotFound, discord.Forbidden):
        pass

    await okay.bot.db.execute("DELETE FROM entrants WHERE GuildID = ?", okay.guild.id)
    await okay.bot.db.execute("UPDATE gateway SET Active = 0, GateMessageID = NULL WHERE GuildID = ?", okay.guild.id)
    await lc.send(
        f"{okay.bot.cross} The gateway module tripped because {reason}. You will need to fix the problem and re-activate the module to use it again."
    )
