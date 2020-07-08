from discord.ext import commands

from s4 import Config


class Hub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.guild = self.bot.get_guild(Config.HUB_GUILD_ID)

            if self.guild is not None:
                self.commands_channel = self.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
                self.relay_channel = self.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
                self.stdout_channel = self.guild.get_channel(Config.HUB_STDOUT_CHANNEL_ID)

                if self.stdout_channel is not None:
                    await self.stdout_channel.send(self.bot.message.load("online", version=self.bot.version))

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.db.execute("INSERT OR IGNORE INTO system (GuildID) VALUES (?)", guild.id)

        if self.stdout_channel is not None:
            await self.stdout_channel.send(self.bot.message.load("joined guild", bot=self.bot, guild=guild))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM system WHERE GuildID = ?", guild.id)

        if self.stdout_channel is not None:
            await self.stdout_channel.send(self.bot.message.load("left guild", guild=guild))

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild == self.guild and not msg.author.bot and self.bot.user in msg.mentions:
            if msg.channel == self.commands_channel:
                if msg.content.startswith("shutdown"):
                    await self.bot.shutdown()

            elif msg.channel == self.relay_channel:
                # TODO: Add relay system.
                pass


def setup(bot):
    bot.add_cog(Hub(bot))
