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

import typing as t

import discord
from discord.ext import commands

from solaris.utils import LOADING_ICON, SUCCESS_ICON, checks, menu, modules


class SetupMenu(menu.SelectionMenu):
    def __init__(self, ctx):
        pagemap = {
            "header": "Setup",
            "title": "Hello!",
            "description": "Welcome to the S4 first time setup! You need to run this before you can use most of S4's commands, but you only ever need to run once.\n\nIn order to operate effectively in your server, S4 needs to create a few things:",
            "thumbnail": ctx.bot.user.avatar_url,
            "fields": [
                [
                    "A log channel",
                    "This will be called s4-logs and will be placed directly under the channel you run the setup in. This channel is what S4 will use to communicate important information to you, so it is recommended you only allow server moderators access to it. You will be able to change what S4 uses as the log channel later.",
                    False,
                ],
                [
                    "An admin role",
                    "This will be called S4 Administrator and will be placed at the bottom of the role hierarchy. This role does not provide members any additional access to the server, but does allow them to use S4's configuration commands. Server administrators do not need this role to configure S4. You will be able to change what S4 uses as the admin role later.",
                    False,
                ],
                [
                    "Ready?",
                    f"If you are ready to run the setup, select {ctx.bot.tick}. To exit the setup without changing anything select {ctx.bot.cross}.",
                    False,
                ],
            ],
        }
        super().__init__(ctx, ["confirm", "cancel"], pagemap, timeout=120.0)

    async def start(self):
        r = await super().start()

        if r == "confirm":
            pagemap = {
                "header": "Setup",
                "description": "Please wait... This should only take a few seconds.",
                "thumbnail": LOADING_ICON,
            }
            await self.switch(pagemap, clear_reactions=True)
            await self.run()
        elif r == "cancel":
            await self.stop()

    async def run(self):
        if not await modules.retrieve.system__logchannel(self.bot, self.ctx.guild):
            if self.ctx.guild.me.guild_permissions.manage_channels:
                lc = await self.ctx.guild.create_text_channel(
                    name="s4-logs",
                    category=self.ctx.channel.category,
                    position=self.ctx.channel.position,
                    topic=f"Log output for {self.ctx.guild.me.mention}",
                    reason="Needed for S4 log output.",
                )
                await self.bot.db.execute(
                    "UPDATE system SET DefaultLogChannelID = ?, LogChannelID = ? WHERE GuildID = ?",
                    lc.id,
                    lc.id,
                    self.ctx.guild.id,
                )
                await lc.send(f"{self.bot.tick} The log channel has been created and set to {lc.mention}.")
            else:
                await self.switch("setup log channel failed", clear_reactions=True)

        if not await modules.retrieve.system__adminrole(self.bot, self.ctx.guild):
            if self.ctx.guild.me.guild_permissions.manage_roles:
                ar = await self.ctx.guild.create_role(
                    name="S4 Administrator",
                    permissions=discord.Permissions(permissions=0),
                    reason="Needed for S4 configuration.",
                )
                await self.bot.db.execute(
                    "UPDATE system SET DefaultAdminRoleID = ?, AdminRoleID = ? WHERE GuildID = ?",
                    ar.id,
                    ar.id,
                    self.ctx.guild.id,
                )
                await lc.send(f"{self.bot.tick} The admin role has been created and set to {ar.mention}.")
            else:
                await self.switch("setup admin role failed", clear_reactions=True)

        await self.complete()

    async def configure_modules(self):
        await self.complete()

    async def complete(self):
        pagemap = {
            "header": "Setup",
            "title": "First time setup complete",
            "description": "Congratulations - the first time setup has been completed! You can now use all of S4's commands, and activate all of S4's modules.\n\nEnjoy using S4!",
            "thumbnail": SUCCESS_ICON,
        }
        await modules.config._system__runfts(self.bot, self.ctx.channel, 1)
        await self.switch(pagemap, clear_reactions=True)


class Modules(commands.Cog):
    """Configure, activate, and deactivate S4 modules."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="setup", help="Runs the first time setup.")
    @checks.bot_has_booted()
    @checks.first_time_setup_has_not_run()
    @checks.author_can_configure()
    async def setup_command(self, ctx):
        await SetupMenu(ctx).start()

    @commands.command(
        name="config", aliases=["set"], help="Configures S4; use `help config` to bring up a special help menu."
    )
    @checks.bot_has_booted()
    @checks.first_time_setup_has_run()
    @checks.author_can_configure()
    async def config_command(
        self,
        ctx,
        module: str,
        attr: str,
        objects: commands.Greedy[t.Union[discord.TextChannel, discord.Role]],
        *,
        text: t.Optional[t.Union[int, str]],
    ):
        if module.startswith("_") or attr.startswith("_"):
            await ctx.send(f"{self.bot.cross} The module or attribute you are trying to access is non-configurable.")
        elif (func := getattr(modules.config, f"{module}__{attr}", None)) is not None:
            await func(self.bot, ctx.channel, (objects[0] if len(objects) == 1 else objects) or text)
        else:
            await ctx.send(f"{self.bot.cross} Invalid module or attribute.")

    @commands.command(
        name="retrieve",
        aliases=["get"],
        help="Retrieves attribute information for a module. Note that the output is raw, so some attributes may appear to have strange or incorrect values when in reality they are fine.",
    )
    @checks.bot_has_booted()
    @checks.first_time_setup_has_run()
    @checks.author_can_configure()
    async def retrieve_command(self, ctx, module: str, attr: str):
        if module.startswith("_") or attr.startswith("_"):
            await ctx.send(f"{self.bot.cross} The module or attribute you are trying to access is non-configurable.")
        elif (func := getattr(modules.retrieve, f"{module}__{attr}", None)) is not None:
            value = v.mention if hasattr((v := await func(self.bot, ctx.guild)), "mention") else v
            await ctx.send(f"{self.bot.info} Value of {attr}: {value}")
        else:
            await ctx.send(f"{self.bot.cross} Invalid module or attribute.")

    @commands.command(name="activate", aliases=["enable"], help="Activates a module.")
    @checks.bot_is_ready()
    @checks.log_channel_is_set()
    @checks.first_time_setup_has_run()
    @checks.author_can_configure()
    async def activate_command(self, ctx, module: str):
        if module.startswith("_"):
            await ctx.send(f"{self.bot.cross} The module you are trying to access is non-configurable.")
        elif (func := getattr(modules.activate, module, None)) is not None:
            await func(ctx)
        else:
            await ctx.send(f"{self.bot.cross} That module either does not exist, or can not be activated.")

    @commands.command(name="deactivate", aliases=["disable"], help="Deactivates a module.")
    @checks.bot_is_ready()
    @checks.log_channel_is_set()
    @checks.first_time_setup_has_run()
    @checks.author_can_configure()
    async def deactivate_command(self, ctx, module: str):
        if module.startswith("_"):
            await ctx.send(f"{self.bot.cross} The module you are trying to access is non-configurable.")
        elif (func := getattr(modules.deactivate, module, None)) is not None:
            await func(ctx)
        else:
            await ctx.send(f"{self.bot.cross} That module either does not exist, or can not be deactivated.")

    @commands.command(
        name="restart", help="Restarts a module. This is a shortcut command which calls `deactivate` then `activate`."
    )
    @checks.bot_is_ready()
    @checks.log_channel_is_set()
    @checks.first_time_setup_has_run()
    @checks.author_can_configure()
    async def restart_command(self, ctx, module: str):
        if module.startswith("_"):
            await ctx.send(f"{self.bot.cross} The module you are trying to access is non-configurable.")
        elif (dfunc := getattr(modules.deactivate, module, None)) is not None and (
            afunc := getattr(modules.activate, module, None)
        ) is not None:
            await dfunc(ctx)
            await afunc(ctx)
        else:
            await ctx.send(f"{self.bot.cross} That module either does not exist, or can not be restarted.")


def setup(bot):
    bot.add_cog(Modules(bot))
