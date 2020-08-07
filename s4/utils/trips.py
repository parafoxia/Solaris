import discord

from s4.utils.modules import retrieve


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
