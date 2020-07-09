import json
from datetime import datetime, timedelta
from os import path
from time import time
from traceback import format_exc

import aiofiles
import aiofiles.os  # This is necessary... :pepegaface:
from discord import File, Forbidden, HTTPException
from discord.ext import commands

from s4.utils import chron, string


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def error(self, err, *args, **kwargs):
        ref = await self.record_error(args[0] if len(args) > 0 else None)
        hub = self.bot.get_cog("Hub")

        if (sc := getattr(hub, "stdout_channel", None)) is not None:
            await sc.send(self.bot.message.load("something went wrong", ref=ref))

        if err == "on_command_error":
            await args[0].send(self.bot.message.load("command went wrong", ref=ref))

        raise  # Re-raises the last known exception.

    async def command_error(self, ctx, exc):
        if isinstance(exc, commands.CommandNotFound):
            pass

        # Custom check failure handling.
        elif hasattr(exc, "key"):
            await ctx.send(self.bot.message.load(exc.key, **exc.kwargs))

        elif isinstance(exc, commands.MissingRequiredArgument):
            await ctx.send(self.bot.message.load("missing required argument", exc=exc, cmd=ctx.command))

        elif isinstance(exc, commands.BadArgument):
            await ctx.send(self.bot.message.load("bad argument", cmd=ctx.command))

        elif isinstance(exc, commands.TooManyArguments):
            await ctx.send(self.bot.message.load("too many arguments", cmd=ctx.command))

        elif isinstance(exc, commands.MissingPermissions):
            await ctx.send(
                self.bot.message.load(
                    "missing permissions",
                    missing_perms=string.list_of(
                        [str(perm.replace("_", " ")).title() for perm in exc.missing_perms], sep="or"
                    ),
                )
            )

        elif isinstance(exc, commands.BotMissingPermissions):
            try:
                await ctx.send(
                    self.bot.message.load(
                        "bot missing permissions",
                        missing_perms=string.list_of(
                            [str(perm.replace("_", " ")).title() for perm in exc.missing_perms], sep="or"
                        ),
                    )
                )
            except Forbidden:
                # If S4 does not have the Send Messages permission
                # (might redirect this to log channel once it's set up).
                pass

        elif isinstance(exc, commands.NotOwner):
            await ctx.send(self.bot.message.load("not owner"))

        elif isinstance(exc, commands.CommandOnCooldown):
            await ctx.send(
                self.bot.message.load(
                    f"command on {str(exc.cooldown.type).split('.')[-1]} cooldown",
                    length=chron.long_delta(timedelta(seconds=exc.retry_after)),
                )
            )

        elif isinstance(exc, commands.InvalidEndOfQuotedStringError):
            await ctx.send(self.bot.message.load("invalid end of quoted string error", exc=exc))

        elif isinstance(exc, commands.ExpectedClosingQuoteError):
            await ctx.send(self.bot.message.load("expected closing quote error"))

        # Base errors.
        elif isinstance(exc, commands.UserInputError):
            await ctx.send(self.bot.message.load("user input error"))

        elif isinstance(exc, commands.CheckFailure):
            await ctx.send(self.bot.message.load("check failure"))

        # Non-command errors.
        elif (original := getattr(exc, "original", None)) is not None:
            if isinstance(original, HTTPException):
                await ctx.send(self.bot.message.load("http exception", status=original.status, text=original.text))

            else:
                raise original

        else:
            raise exc

    async def record_error(self, ctx):
        if ctx is not None:
            content = ctx.message.content
        else:
            content = "Not applicable."

        ref = hex(int(time() * 1e7))[2:]
        await self.bot.db.execute(
            "INSERT INTO errors (Ref, Content, Traceback) VALUES (?, ?, ?)", ref, content, format_exc()
        )
        return ref

    @commands.command(name="recallerror", aliases=["err"])
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def recall_error(self, ctx, ref: str):
        content, error_time, traceback = await self.bot.db.record(
            "SELECT Content, ErrorTime, Traceback FROM errors WHERE Ref = ?", ref
        )

        path = f"{self.bot._dynamic}/{ref}.txt"
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            text = f"Time of error:\n{error_time}\n\nContent:\n{content}\n\n{traceback}"
            await f.write(text)

        await ctx.send(file=File(path))
        await aiofiles.os.remove(path)


def setup(bot):
    bot.add_cog(Error(bot))
