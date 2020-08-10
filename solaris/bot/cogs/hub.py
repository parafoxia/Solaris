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

from discord.ext import commands

from solaris import Config


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
                    await self.stdout_channel.send(
                        f"{self.bot.info} Solaris is now online! (Version {self.bot.version})"
                    )

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.db.execute("INSERT OR IGNORE INTO system (GuildID) VALUES (?)", guild.id)
        await self.bot.db.execute("INSERT OR IGNORE INTO gateway (GuildID) VALUES (?)", guild.id)

        if self.stdout_channel is not None:
            await self.stdout_channel.send(
                f"{self.bot.info} Joined guild! Nº: {self.bot.guild_count:,} • Name: {guild.name} • Members: {guild.member_count:,} • ID: {guild.id}"
            )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM system WHERE GuildID = ?", guild.id)
        await self.bot.db.execute("DELETE FROM gateway WHERE GuildID = ?", guild.id)

        if self.stdout_channel is not None:
            await self.stdout_channel.send(
                f"{self.bot.info} Left guild. Name: {guild.name} • Members: {guild.member_count:,} • ID: {guild.id}"
            )

    @commands.Cog.listener()
    async def on_message(self, msg):
        if self.bot.ready.hub:
            if msg.guild == self.guild and not msg.author.bot and self.bot.user in msg.mentions:
                if msg.channel == self.commands_channel:
                    if msg.content.startswith("shutdown"):
                        await self.bot.shutdown()

                elif msg.channel == self.relay_channel:
                    # TODO: Add relay system.
                    pass


def setup(bot):
    bot.add_cog(Hub(bot))
