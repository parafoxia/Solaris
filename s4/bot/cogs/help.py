import typing as t

from discord.ext import commands

from s4.utils import HELPS, converters, menu


class HelpMenu(menu.MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @staticmethod
    def syntax(cmd):
        invokations = "|".join([f"{cmd}", *cmd.aliases])
        return f"```@S4 {invokations} {cmd.signature}```"

    @staticmethod
    def module_description(cog):
        return HELPS[cog.qualified_name.lower()].get("_", "No module description available.")

    @staticmethod
    def brief(cog, cmd):
        return (
            HELPS[cog.qualified_name.lower()][cmd.name]
            .get("description", "No description available.")
            .split(".", maxsplit=1)[0]
        )

    @staticmethod
    def full_help(help_entry):
        return help_entry.get("description", "No description available.")

    @staticmethod
    def user_requirements(help_entry):
        return "\n".join(help_entry.get("user requirements", ["None"]))

    @staticmethod
    def bot_requirements(help_entry):
        return "\n".join(help_entry.get("bot requirements", []))

    async def get_command_mapping(self, ctx):
        mapping = {}

        for cog in self.bot.cogs.values():
            cog_help = HELPS.get(cog.qualified_name.lower(), None)

            if cog_help is not None:
                cog_cmds = []
                for cmd in filter(lambda c: c.name in cog_help.keys(), cog.get_commands()):
                    try:
                        await cmd.can_run(ctx)
                        cog_cmds.append(cmd)
                    except commands.CommandError:
                        pass

                if cog_cmds:
                    mapping.update({cog: cog_cmds})

        return mapping

    @commands.command(name="help")
    async def help_command(self, ctx, cmd: t.Optional[converters.Command]):
        if cmd is None:
            pagemaps = []

            for cog, cmds in (await self.get_command_mapping(ctx)).items():
                pagemaps.append(
                    {
                        "header": "Help",
                        "title": f"The `{cog.qualified_name.lower()}` module",
                        "description": self.module_description(cog),
                        "thumbnail": self.bot.user.avatar_url,
                        "fields": [(self.brief(cog, cmd), self.syntax(cmd), False) for cmd in cmds],
                    }
                )

            await HelpMenu(ctx, pagemaps).start()

        else:
            if not cmd:
                await ctx.send(f"{self.bot.cross} S4 has no commands or aliases with that name.")
            elif cmd.name == "config":
                pass
            else:
                if (help_entry := HELPS.get(cmd.cog.qualified_name.lower(), {}).get(cmd.name)) is None:
                    await ctx.send(f"{self.bot.cross} No help is available for that command.")
                else:
                    await ctx.send(
                        embed=self.bot.embed.build(
                            ctx=ctx,
                            header="Help",
                            description=self.full_help(help_entry),
                            thumbnail=self.bot.user.avatar_url,
                            syntax=self.syntax(cmd),
                            user_reqs=self.user_requirements(help_entry),
                            bot_reqs=self.bot_requirements(help_entry),
                            fields=[
                                ["Syntax (<required> • [optional])", self.syntax(cmd), False],
                                ["User requirements", self.user_requirements(help_entry), False],
                                [
                                    "S4 requirements",
                                    f"Read Messages\nSend Messages\n{self.bot_requirements(help_entry)}",
                                    False,
                                ],
                            ],
                        )
                    )


def setup(bot):
    bot.add_cog(Help(bot))
