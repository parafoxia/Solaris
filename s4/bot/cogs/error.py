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

import datetime as dt
import json
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

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    async def error(self, err, *args, **kwargs):
        ref = await self.record_error(args[0] if len(args) > 0 else None)
        hub = self.bot.get_cog("Hub")

        if (sc := getattr(hub, "stdout_channel", None)) is not None:
            await sc.send(f"{self.bot.cross} Something went wrong (ref: {ref}).")

        if err == "on_command_error":
            prefix = await self.bot.prefix(args[0].guild)
            await args[0].send(
                f"{self.bot.cross} Something went wrong (ref: {ref}). Quote this reference in the support server, which you can get a link for by using `{prefix}support`."
            )

        raise  # Re-raises the last known exception.

    async def command_error(self, ctx, exc):
        prefix = await self.bot.prefix(ctx.guild)

        if isinstance(exc, commands.CommandNotFound):
            pass

        # Custom check failure handling.
        elif hasattr(exc, "msg"):
            await ctx.send(f"{self.bot.cross} {exc.msg}")

        elif isinstance(exc, commands.MissingRequiredArgument):
            await ctx.send(
                f"{self.bot.cross} No `{exc.param.name}` argument was passed, despite being required. Use `{prefix}help {ctx.command}` for more information."
            )

        elif isinstance(exc, commands.BadArgument):
            await ctx.send(
                f"{self.bot.cross} One or more arguments are invalid. Use `{prefix}help {ctx.command}` for more information."
            )

        elif isinstance(exc, commands.TooManyArguments):
            await ctx.send(
                f"{self.bot.cross} Too many arguments have been passed. Use `{prefix}help {ctx.command}` for more information.",
            )

        elif isinstance(exc, commands.MissingPermissions):
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms], sep="or")
            await ctx.send(
                f"{self.bot.cross} You do not have the {mp} permission(s), which are required to use this command."
            )

        elif isinstance(exc, commands.BotMissingPermissions):
            try:
                mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms], sep="or")
                await ctx.send(
                    f"{self.bot.cross} S4 does not have the {mp} permission(s), which are required to use this command."
                )
            except Forbidden:
                # If S4 does not have the Send Messages permission
                # (might redirect this to log channel once it's set up).
                pass

        elif isinstance(exc, commands.NotOwner):
            await ctx.send(f"{self.bot.cross} That command can only be used by S4's owner.")

        elif isinstance(exc, commands.CommandOnCooldown):
            # Hooray for discord.py str() logic.
            cooldown_texts = {
                "BucketType.user": "{} You can not use that commands for another {}.",
                "BucketType.guild": "{} That command can not be used in this server for another {}.",
                "BucketType.channel": "{} That command can not be used in this channel for another {}.",
                "BucketType.member": "{} You can not use that command in this server for another {}.",
                "BucketType.category": "{} That command can not be used in this category for another {}.",
            }
            await ctx.send(
                cooldown_texts[str(exc.cooldown.type)].format(
                    self.bot.cross, chron.long_delta(dt.timedelta(seconds=exc.retry_after))
                )
            )

        elif isinstance(exc, commands.InvalidEndOfQuotedStringError):
            await ctx.send(
                f"{self.bot.cross} S4 expected a space after the closing quote, but found a(n) `{exc.char}` instead."
            )

        elif isinstance(exc, commands.ExpectedClosingQuoteError):
            await ctx.send(f"{self.bot.cross} S4 expected a closing quote character, but did not find one.")

        # Base errors.
        elif isinstance(exc, commands.UserInputError):
            await ctx.send(
                f"{self.bot.cross} There was an unhandled user input problem (probably argument passing error). Use `{prefix}help {ctx.command}` for more information."
            )

        elif isinstance(exc, commands.CheckFailure):
            await ctx.send(
                f"{self.bot.cross} There was an unhandled command check error (probably missing privileges). Use `{prefix}help {ctx.command}` for more information."
            )

        # Non-command errors.
        elif (original := getattr(exc, "original", None)) is not None:
            if isinstance(original, HTTPException):
                await ctx.send(
                    f"{self.bot.cross} A HTTP exception occurred ({original.status})\n```{original.text}```"
                )
            else:
                raise original

        else:
            raise exc

    async def record_error(self, obj):
        ref = hex(int(time() * 1e7))[2:]
        await self.bot.db.execute(
            "INSERT INTO errors (Ref, Cause, Traceback) VALUES (?, ?, ?)", ref, f"{obj!r}", format_exc()
        )
        return ref

    @commands.command(name="recallerror", aliases=["err"])
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def recallerror_command(self, ctx, ref: str):
        cause, error_time, traceback = await self.bot.db.record(
            "SELECT Cause, ErrorTime, Traceback FROM errors WHERE Ref = ?", ref
        )

        path = f"{self.bot._dynamic}/{ref}.txt"
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            text = f"Time of error:\n{error_time}\n\nCause:\n{cause}\n\n{traceback}"
            await f.write(text)

        await ctx.send(file=File(path))
        await aiofiles.os.remove(path)


def setup(bot):
    bot.add_cog(Error(bot))
