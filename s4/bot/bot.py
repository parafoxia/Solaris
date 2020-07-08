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
        self.emoji = EmojiGetter(self)
        self.embed = EmbedConstructor(self)
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
            print(f" Loading `{cog}` cog...", end="")
            self.load_extension(f"s4.bot.cogs.{cog}")
            print(f"done.")

        print("Setup complete.")

    def run(self):
        self.setup()

        print("Running bot...")
        print(" Connectiong to Discord...", end="")
        super().run(Config.TOKEN, reconnect=True)

    async def shutdown(self):
        print("Shutting down...")
        print(" Shutting down scheduler...", end="")
        self.scheduler.shutdown()
        print("done.")

        print(" Closing database connection...", end="")
        await self.db.close()
        print("done.")

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
            print("done.")
            print(" Connecting to database...", end="")
            await self.db.connect()
            print("done.")
            print(" Readying...", end="")
        else:
            print(f"> Bot connected (DWSP latency: {self.latency*1000:,.0f} ms).")

    async def on_disconnect(self):
        print("> Bot disconnected.")

    async def on_ready(self):
        if not self.ready.booted:
            print("done.")
            print(" Starting scheduler...", end="")
            self.scheduler.start()
            print(f"done ({len(self.scheduler.get_jobs()):,} job(s)).")

            print(" Syncing database...", end="")
            await self.db.sync()
            print("done.")

            print(" Bot ready.")
            self.ready.booted = True

        else:
            print(f"> Bot reconnected (DWSP latency: {self.latency*1000:,.0f} ms).")

        await self.presence.set()

    # async def on_error(self, err, *args, **kwargs):
    #     pass

    # async def on_command_error(self, ctx, exc):
    #     pass

    async def command_prefix(self, bot, msg):
        # TODO: Re-add support for custom prefixes.
        return commands.when_mentioned_or(Config.DEFAULT_PREFIX)(bot, msg)

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            if self.ready.booted:
                await self.invoke(ctx)
            else:
                # TODO: Change this to JSON message implementation.
                await ctx.send(self.message.load("not ready"))

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)
