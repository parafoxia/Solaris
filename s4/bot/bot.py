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

import os
import subprocess as sp
from pathlib import Path

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from s4 import Config, utils
from s4.db import Database
from s4.utils import loc


class Bot(commands.Bot):
    def __init__(self, version):
        self.version = version
        self._cogs = [p.stem for p in Path(".").glob("./s4/bot/cogs/*.py")]
        self._dynamic = "./s4/data/dynamic"
        self._static = "./s4/data/static"
        self._python_lines = loc.python_lines()
        self._json_lines = loc.json_lines()
        self._sql_lines = loc.sql_lines()

        self.scheduler = AsyncIOScheduler()
        self.db = Database(self)
        self.embed = utils.EmbedConstructor(self)
        self.emoji = utils.EmojiGetter(self)
        self.presence = utils.PresenceSetter(self)
        self.ready = utils.Ready(self)

        super().__init__(command_prefix=self.command_prefix, case_insensitive=True, status=discord.Status.dnd)

    def setup(self):
        print("Running setup...")

        for cog in self._cogs:
            self.load_extension(f"s4.bot.cogs.{cog}")
            print(f" Loaded `{cog}` cog.")

        print("Setup complete.")

    def run(self):
        self.setup()

        print("Running bot...")
        super().run(Config.TOKEN, reconnect=True)

    async def shutdown(self):
        print("Shutting down...")
        self.scheduler.shutdown()
        print(" Shut down scheduler.")

        await self.db.close()
        print(" Closed database connection.")

        hub = self.get_cog("Hub")
        if (sc := getattr(hub, "stdout_channel", None)) is not None:
            await sc.send(f"{self.info} S4 is shutting down. (Version {self.version})")

        print(" Closing connection to Discord...")
        await self.logout()

    async def on_connect(self):
        if not self.ready.booted:
            print(f" Connected to Discord (latency: {self.latency*1000:,.0f} ms).")
            await self.db.connect()
            print(" Connected to database.")

    async def on_resumed(self):
        print("Bot resumed.")

    async def on_disconnect(self):
        print("Bot disconnected.")

    async def on_ready(self):
        if not self.ready.booted:
            print(" Readied.")
            self.client_id = (await self.application_info()).id

            self.scheduler.start()
            print(f" Scheduler started ({len(self.scheduler.get_jobs()):,} job(s)).")

            await self.db.sync()
            self.ready.synced = True
            print(" Synchronised database.")

            self.ready.booted = True
            print(" Bot booted.")

        else:
            print("Bot reconnected.")

        await self.presence.set()

    async def on_error(self, err, *args, **kwargs):
        error = self.get_cog("Error")
        await error.error(err, *args, **kwargs)

    async def on_command_error(self, ctx, exc):
        error = self.get_cog("Error")
        await error.command_error(ctx, exc)

    async def prefix(self, guild):
        return await self.db.field("SELECT Prefix FROM system WHERE GuildID = ?", guild.id)

    async def command_prefix(self, bot, msg):
        prefix = await self.prefix(msg.guild)
        return commands.when_mentioned_or(prefix or Config.DEFAULT_PREFIX)(bot, msg)

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            if self.ready.booted:
                await self.invoke(ctx)
            else:
                await ctx.send(
                    f"{self.cross} S4 is still booting and is not ready to receive commands. Please try again later."
                )

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)

    @property
    def guild_count(self):
        return len(self.guilds)

    @property
    def user_count(self):
        return len(self.users)

    @property
    def command_count(self):
        return len(self.commands)

    @property
    def admin_invite(self):
        return discord.utils.oauth_url(self.client_id, permissions=discord.Permissions(administrator=True))

    @property
    def non_admin_invite(self):
        return discord.utils.oauth_url(
            self.client_id,
            permissions=discord.Permissions(
                manage_roles=True,
                manage_channels=True,
                kick_members=True,
                ban_members=True,
                read_messages=True,
                send_messages=True,
                manage_messages=True,
                embed_links=True,
                read_message_history=True,
                use_external_emojis=True,
                add_reactions=True,
            ),
        )

    @property
    def tick(self):
        return self.emoji.mention("confirm")

    @property
    def cross(self):
        return self.emoji.mention("cancel")

    @property
    def info(self):
        return self.emoji.mention("info")

    async def grab_user(self, arg):
        # A convenience method that initially calls get, and falls back to fetch.
        try:
            return self.get_user(arg) or await self.fetch_user(arg)
        except (ValueError, discord.NotFound):
            return None

    async def grab_channel(self, arg):
        # A convenience method that initially calls get, and falls back to fetch.
        try:
            return self.get_channel(arg) or await self.fetch_channel(arg)
        except (ValueError, discord.NotFound):
            return None

    async def grab_guild(self, arg):
        # A convenience method that initially calls get, and falls back to fetch.
        try:
            return self.get_guild(arg) or await self.fetch_guild(arg)
        except (ValueError, discord.NotFound):
            return None
