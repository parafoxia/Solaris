import typing as t

from discord.ext import commands

from s4.utils import HELPS, converters, menu


class HelpMenu(menu.MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        spm = ctx.bot.embed.get_pagemap("help menu closed", thumbnail=ctx.bot.user.avatar_url)
        tpm = ctx.bot.embed.get_pagemap("help menu timed out", thumbnail=ctx.bot.user.avatar_url)

        super().__init__(ctx, pagemaps, spm, tpm, timeout=120.0)

    async def start(self):
        r = await super().start()


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
        return HELPS["__modules__"].get(cog.qualified_name.lower(), "No module description available.")

    @staticmethod
    def brief(cmd):
        # This goes on the basis the cmd is definitely in HELPS (which should be guaranteed).
        return HELPS[cmd.name].get("description", "No description available.").split(".", maxsplit=1)[0]

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
            cog_cmds = []

            for cmd in filter(lambda c: c.name in HELPS.keys(), cog.get_commands()):
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
                        "fields": [(self.brief(cmd), self.syntax(cmd), False) for cmd in cmds],
                    }
                )

            await HelpMenu(ctx, pagemaps).start()

        else:
            if not cmd:
                await ctx.send(self.bot.message.load("command does not exist"))
            elif cmd.name == "config":
                pass
            else:
                if (help_entry := HELPS.get(cmd.name, None)) is None:
                    await ctx.send(self.bot.message.load("no help available"))
                else:
                    await ctx.send(
                        embed=self.bot.embed.load(
                            "help command",
                            ctx=ctx,
                            thumbnail=self.bot.user.avatar_url,
                            description=self.full_help(help_entry),
                            syntax=self.syntax(cmd),
                            user_reqs=self.user_requirements(help_entry),
                            bot_reqs=self.bot_requirements(help_entry),
                        )
                    )


def setup(bot):
    bot.add_cog(Help(bot))
