from discord.ext import commands

from s4 import Config


class Hub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.guild = self.bot.get_guild(Config.HUB_GUILD_ID)
            self.commands_channel = self.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
            self.relay_channel = self.guild.get_channel(Config.HUB_COMMANDS_CHANNEL_ID)
            self.stdout_channel = self.guild.get_channel(Config.HUB_STDOUT_CHANNEL_ID)

            await self.stdout_channel.send(self.bot.message.load("online", version=self.bot.version))
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if not msg.author.bot and (self.bot.user in message.mentions or "all" in message.content):
            if message.channel == self.commands_channel:
                if message.content.startswith("shutdown"):
                    await self.bot.shutdown()

            elif message.channel == self.relay_channel:
                # TODO: Add relay system.
                pass


def setup(bot):
    bot.add_cog(Hub(bot))
