from os import path

from aiosqlite import connect
from apscheduler.triggers.cron import CronTrigger


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.db_path = f"{self.bot._dynamic}/database.db3"
        self.build_path = f"{self.bot._static}/build.sql"
        self._calls = 0

        self.bot.scheduler.add_job(self.commit, CronTrigger(second=0))

    async def connect(self):
        if not path.isdir(self.bot._dynamic):
            # If this directory does not exist, we need to create it.
            from os import makedirs

            makedirs(self.bot._dynamic)

        self.cxn = await connect(self.db_path)
        await self.execute("pragma journal_mode=wal")
        await self.executescript(self.build_path)
        await self.commit()

    async def commit(self):
        if self.bot.ready.ok:
            await self.execute("UPDATE bot SET Value = CURRENT_TIMESTAMP WHERE Key = 'last commit'")

        await self.cxn.commit()

    async def close(self):
        await self.commit()
        await self.cxn.close()

    async def sync(self):
        # Insert.
        await self.executemany("INSERT OR IGNORE INTO system (GuildID) VALUES (?)", [(g.id,) for g in self.bot.guilds])

        # Remove.
        stored = await self.column("SELECT GuildID FROM system")
        member_of = [g.id for g in self.bot.guilds]
        removals = [(g_id,) for g_id in set(stored) - set(member_of)]
        await self.executemany("DELETE FROM system WHERE GuildID = ?", removals)

        # Commit.
        await self.commit()

    async def field(self, sql, *values):
        cur = await self.cxn.execute(sql, tuple(values))
        self._calls += 1

        if (row := await cur.fetchone()) is not None:
            return row[0]

    async def record(self, sql, *values):
        cur = await self.cxn.execute(sql, tuple(values))
        self._calls += 1

        return await cur.fetchone()

    async def records(self, sql, *values):
        cur = await self.cxn.execute(sql, tuple(values))
        self._calls += 1

        return await cur.fetchall()

    async def column(self, sql, *values):
        cur = await self.cxn.execute(sql, tuple(values))
        self._calls += 1

        return [row[0] for row in await cur.fetchall()]

    async def execute(self, sql, *values):
        cur = await self.cxn.execute(sql, tuple(values))
        self._calls += 1

    async def executemany(self, sql, valueset):
        await self.cxn.executemany(sql, valueset)
        self._calls += 1  # NOTE: Should this be `len(valueset)`?

    async def executescript(self, path):
        with open(path, "r", encoding="utf-8") as script:
            await self.cxn.executescript(script.read())

        self._calls += 1  # NOTE: Should this be different?
