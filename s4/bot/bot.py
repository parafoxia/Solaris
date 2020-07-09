from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Status
from discord.ext import commands

from s4 import Config
from s4.db import Database
from s4.utils import EmbedConstructor, EmojiGetter, MessageConstructor, PresenceSetter, Ready


class Bot(commands.Bot):
    def __init__(self, version):
        self.version = version
        self._cogs = [p.stem for p in Path(".").glob("./s4/bot/cogs/*.py")]
        self._dynamic = "./s4/data/dynamic"
        self._static = "./s4/data/static"

        self.scheduler = AsyncIOScheduler()
        self.db = Database(self)
        self.embed = EmbedConstructor(self)
        self.emoji = EmojiGetter(self)
        self.message = MessageConstructor(self)
        self.presence = PresenceSetter(self)
        self.ready = Ready(self)

        super().__init__(command_prefix=self.command_prefix, case_insensitive=True, status=Status.dnd)

    @property
    def guild_count(self):
        return len(self.guilds)

    @property
    def user_count(self):
        return len(self.users)

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
            await sc.send(self.message.load("shutting down", version=self.version))

        print(" Closing connection to Discord...")
        await super().close()

    async def close(self):
        print("Closing on keyboard interrupt...")
        await self.shutdown()

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
            self.scheduler.start()
            print(f" Scheduler started ({len(self.scheduler.get_jobs()):,} job(s)).")

            await self.db.sync()
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
                # TODO: Change this to JSON message implementation.
                await ctx.send(self.message.load("bot is not ready"))

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)
