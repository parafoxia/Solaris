import discord

from s4.utils.modules import retrieve


async def gateway(ctx):
    async with ctx.typing():
        active, rc_id, gm_id = await ctx.bot.db.record(
            "SELECT Active, RulesChannelID, GateMessageID FROM gateway WHERE GuildID = ?", ctx.guild.id
        )

        if not active:
            await ctx.send(f"{ctx.bot.cross} The gateway module is already inactive.")
        else:
            try:
                gm = await ctx.bot.get_channel(rc_id).fetch_message(gm_id)
                await gm.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

            await ctx.bot.db.execute("DELETE FROM entrants WHERE GuildID = ?", ctx.guild.id)
            await ctx.bot.db.execute(
                "UPDATE gateway SET Active = 0, GateMessageID = NULL WHERE GuildID = ?", ctx.guild.id
            )

            await ctx.send(f"{ctx.bot.tick} The gateway module has been deactivated.")
            lc = await retrieve.log_channel(ctx.bot, ctx.guild)
            await lc.send(f"{ctx.bot.info} The gateway module has been deactivated.")


async def everything(ctx):
    await gateway(ctx)
