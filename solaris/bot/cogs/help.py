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

import typing as t
from collections import defaultdict

from discord.ext import commands

from solaris.utils import checks, converters, menu, modules, string


class HelpMenu(menu.MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


class ConfigHelpMenu(menu.NumberedSelectionMenu):
    def __init__(self, ctx):
        pagemap = {
            "header": "Help",
            "title": "Configuration help",
            "description": "Select the module you want to configure.",
            "thumbnail": ctx.bot.user.avatar_url,
        }
        super().__init__(
            ctx,
            [cog.qualified_name.lower() for cog in ctx.bot.cogs.values() if getattr(cog, "configurable", False)],
            pagemap,
        )

    async def start(self):
        if (r := await super().start()) is not None:
            await self.display_help(r)

    async def display_help(self, module):
        prefix = await self.bot.prefix(self.ctx.guild)

        await self.message.clear_reactions()
        await self.message.edit(
            embed=self.bot.embed.build(
                ctx=self.ctx,
                header="Help",
                title=f"Configuration help for {module}",
                description=(
                    list(filter(lambda c: c.qualified_name.lower() == module, self.bot.cogs.values())).pop().__doc__
                ),
                thumbnail=self.bot.user.avatar_url,
                fields=(
                    (
                        (doc := func.__doc__.split("\n", maxsplit=1))[0],
                        f"{doc[1]}\n`{prefix}config {module} {name[len(module)+2:]}`",
                        False,
                    )
                    for name, func in filter(lambda f: module in f[0], modules.config.__dict__.items())
                    if not name.startswith("_")
                ),
            )
        )


class Help(commands.Cog):
    """Assistance with using a configuring Solaris."""

    def __init__(self, bot):
        self.bot = bot

        self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @staticmethod
    async def basic_syntax(ctx, cmd, prefix):
        try:
            await cmd.can_run(ctx)
            return f"{prefix}{cmd.name}" if cmd.parent is None else f"  ↳ {cmd.name}"
        except commands.CommandError:
            return f"{prefix}{cmd.name} (✗)" if cmd.parent is None else f"  ↳ {cmd.name} (✗)"

    @staticmethod
    async def full_syntax(ctx, cmd, prefix):
        invokations = "|".join([cmd.name, *cmd.aliases])
        return f"```{prefix}{invokations} {cmd.signature}```"

    @staticmethod
    async def required_permissions(ctx, cmd):
        try:
            await cmd.can_run(ctx)
            return "Yes"
        except commands.MissingPermissions as exc:
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
            return f"No - You are missing the {mp} permission(s)"
        except commands.BotMissingPermissions as exc:
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
            return f"No - Solaris is missing the {mp} permission(s)"
        except checks.AuthorCanNotConfigure:
            return "No - You are not able to configure Solaris."
        except commands.CommandError:
            return "No - Solaris is not configured properly"

    async def get_command_mapping(self, ctx):
        mapping = defaultdict(list)

        for cog in self.bot.cogs.values():
            if cog.__doc__ is not None:
                for cmd in cog.walk_commands():
                    if cmd.help is not None:
                        mapping[cog].append(cmd)

        return mapping

    @commands.command(
        name="help",
        help="Help with anything Solaris. Passing a command name or alias through will show help with that specific command, while passing no arguments will bring up a general command overview.",
    )
    async def help_command(self, ctx, cmd: t.Optional[converters.Command]):
        prefix = await self.bot.prefix(ctx.guild)

        if cmd is None:
            pagemaps = []

            for cog, cmds in (await self.get_command_mapping(ctx)).items():
                pagemaps.append(
                    {
                        "header": "Help",
                        "title": f"The `{cog.qualified_name.lower()}` module",
                        "description": f"{cog.__doc__}\n\nUse `{prefix}help [command]` for more detailed help on a command. You can not run commands with `(✗)` next to them.",
                        "thumbnail": self.bot.user.avatar_url,
                        "fields": (
                            (
                                f"{len(cmds)} command(s)",
                                "```{}```".format(
                                    "\n".join([await self.basic_syntax(ctx, cmd, prefix) for cmd in cmds])
                                ),
                                False,
                            ),
                        ),
                    }
                )

            await HelpMenu(ctx, pagemaps).start()

        else:
            if not cmd:
                await ctx.send(f"{self.bot.cross} Solaris has no commands or aliases with that name.")
            elif cmd.name == "config":
                await ConfigHelpMenu(ctx).start()
            else:
                await ctx.send(
                    embed=self.bot.embed.build(
                        ctx=ctx,
                        header="Help",
                        description=cmd.help,
                        thumbnail=self.bot.user.avatar_url,
                        fields=(
                            ("Syntax (<required> • [optional])", await self.full_syntax(ctx, cmd, prefix), False),
                            ("On cooldown?", cmd.is_on_cooldown(ctx), False),
                            ("Can be run?", await self.required_permissions(ctx, cmd), False),
                        ),
                    )
                )


def setup(bot):
    bot.add_cog(Help(bot))
