import typing as t

from discord.ext import commands

from s4.utils import converters, menu, string


class HelpMenu(menu.MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


class Help(commands.Cog):
    """This module is aimed at assisting you with using S4."""

    def __init__(self, bot):
        self.bot = bot

        self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @staticmethod
    async def syntax(ctx, cmd):
        invokations = "|".join([f"{cmd}", *cmd.aliases])
        return f"```{await ctx.bot.prefix(ctx.guild)}{invokations} {cmd.signature}```"

    @staticmethod
    async def required_permissions(ctx, cmd):
        try:
            await cmd.can_run(ctx)
            return "You have all the required permissions to run this command."
        except commands.MissingPermissions:
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
            return "You are missing the {mp} permission(s) required to run this command."
        except commands.CommandError:
            return "You are not able to run this command."

    @staticmethod
    async def required_bot_permissions(ctx, cmd):
        try:
            await cmd.can_run(ctx)
            return "S4 has all the required permissions to run this command."
        except commands.MissingPermissions:
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
            return "S4 is missing the {mp} permission(s) required to run this command."
        except commands.CommandError:
            return "S4 is not able to run this command."

    async def get_command_mapping(self, ctx):
        mapping = {}

        for cog in self.bot.cogs.values():
            if cog.__doc__ is not None:
                cog_cmds = []
                for cmd in filter(lambda c: c.help is not None, cog.get_commands()):
                    try:
                        await cmd.can_run(ctx)
                        cog_cmds.append(cmd)
                    except commands.CommandError:
                        pass

                if cog_cmds:
                    mapping.update({cog: cog_cmds})

        return mapping

    @commands.command(
        name="help",
        help="Help with anything S4. Passing a command name or alias through will show help with that specific command, while passing no arguments will bring up a general command overview.",
    )
    async def help_command(self, ctx, cmd: t.Optional[converters.Command]):
        if cmd is None:
            pagemaps = []

            for cog, cmds in (await self.get_command_mapping(ctx)).items():
                pagemaps.append(
                    {
                        "header": "Help",
                        "title": f"The `{cog.qualified_name.lower()}` module",
                        "description": cog.__doc__,
                        "thumbnail": self.bot.user.avatar_url,
                        "fields": [
                            (
                                cmd.help.split(".")[0] if cmd.help is not None else "No help available.",
                                await self.syntax(ctx, cmd),
                                False,
                            )
                            for cmd in cmds
                        ],
                    }
                )

            await HelpMenu(ctx, pagemaps).start()

        else:
            if not cmd:
                await ctx.send(f"{self.bot.cross} S4 has no commands or aliases with that name.")
            elif cmd.name == "config":
                pass
            else:
                await ctx.send(
                    embed=self.bot.embed.build(
                        ctx=ctx,
                        header="Help",
                        description=cmd.help,
                        thumbnail=self.bot.user.avatar_url,
                        fields=[
                            ("Syntax (<required> • [optional])", await self.syntax(ctx, cmd), False),
                            ("On Cooldown?", cmd.is_on_cooldown(ctx), False),
                            ("User requirements", await self.required_permissions(ctx, cmd), False),
                            ("Bot requirements", await self.required_bot_permissions(ctx, cmd), False),
                        ],
                    )
                )


def setup(bot):
    bot.add_cog(Help(bot))
