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

import discord
from discord.ext import commands

import typing as t
from string import ascii_lowercase

from solaris.utils import menu, converters

#MAX_TAGS = 35
MAX_TAGNAME_LENGTH = 25

class HelpMenu(menu.MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)

class Tags(commands.Cog):
    """Commands for creating tags."""
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


    @commands.command(name = "tag", help = "Shows the content of an existing tag.")
    @commands.bot_has_permissions(send_messages = True)
    async def tag_command(self, ctx, tag_name: str):
        if any(c not in ascii_lowercase for c in tag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        tag_content = await self.bot.db.column("SELECT TagContent FROM tags WHERE GuildID = ?", ctx.guild.id)
        tag_names= await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)

        cache = []

        if tag_name not in tag_names:
            await ctx.send(f'{self.bot.cross} The Tag `{tag_name}` does not exist.')
            for x in range(len(tag_names)):
                if tag_names[x][0] == tag_name[0]:
                    cache.append(tag_names[x])
                    return await ctx.send("Did you mean..." + '\n'.join(cache))

        else:
        	content, tag_id = await self.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)

        	await ctx.send(content)


    @commands.group(
        name="tags",
        invoke_without_command=True,
        help="Commands to create tags in the server.",
        )
    @commands.bot_has_permissions(send_messages = True)
    async def tags_group(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        cmds = tuple(sorted(self.bot.get_command("tags").commands, key=lambda c: c.name))

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="Tags",
                thumbnail=self.bot.user.avatar_url,
                description="There are a few different tag methods you can use.",
                fields=(
                    *(
                        (
                            cmd.name.title(),
                            f"{cmd.help} For more infomation, use `{prefix}help tags {cmd.name}`",
                            False,
                        )
                        for cmd in cmds
                    ),
                ),
            )
        )


    @tags_group.command(name = "new", help = "Creates a new tag.")
    @commands.bot_has_permissions(send_messages = True)
    async def tag_create(self, ctx, tag_name: str, *, content):
        if any(c not in ascii_lowercase for c in tag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        if len(tag_name) > MAX_TAGNAME_LENGTH:
            return await ctx.send(
                f"{self.bot.cross} Tag identifiers must not exceed `{MAX_TAGNAME_LENGTH}` characters in length."
            )

        tag_names = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)

        #if len(tag_names) == MAX_TAGS:
            #return await ctx.send(f"{self.bot.cross} You can only set up to {MAX_TAGS} warn types.")

        if tag_name in tag_names:
            prefix = await self.bot.prefix(ctx.guild)
            return await ctx.send(
                f"{self.bot.cross} That tag already exists. You can use `{prefix}tag edit {tag_name}`"
            )

        await self.bot.db.execute(
            "INSERT INTO tags (GuildID, UserID, TagID, TagName, TagContent) VALUES (?, ?, ?, ?, ?)",
            ctx.guild.id,
            ctx.author.id,
            self.bot.generate_id(),
            tag_name,
            content
        )
        await ctx.send(f'{self.bot.tick} The tag `{tag_name}` has been created.')


    @tags_group.command(
        name="edit",
        help="Edits an existing tag.",
    )
    @commands.bot_has_permissions(send_messages = True)
    async def tag_edit(self, ctx, tag_name: str, *, content):
        if any(c not in ascii_lowercase for c in tag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        user_id, tag_id = await self.bot.db.record("SELECT UserID, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)

        if user_id != ctx.author.id:
            return await ctx.send(f"{self.bot.cross} You can't edit others tags. You can only edit your own tags.")

        else:
            tag_content = await self.bot.db.column("SELECT TagContent FROM tags WHERE GuildID = ?", ctx.guild.id)
            tag_names = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)

            if tag_name not in tag_names:
                return await ctx.send(f'{self.bot.cross} The tag `{tag_name}` does not exist.')

            if content in tag_content:
                return await ctx.send(f'{self.bot.cross} That content already exists in this `{tag_name}` tag.')

            await self.bot.db.execute(
                "UPDATE tags SET TagContent = ? WHERE GuildID = ? AND TagName = ?",
                content,
                ctx.guild.id,
                tag_name,
            )

            await ctx.send(
                f"{self.bot.tick} The `{tag_name}` tag's content has been updated."
            )


    @tags_group.command(
        name="delete",
        aliases=["del"],
        help="Deletes an existing tag.",
    )
    @commands.bot_has_permissions(send_messages = True)
    async def tag_delete_command(self, ctx, tag_name: str):
        if any(c not in ascii_lowercase for c in tag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        user_id, tag_id = await self.bot.db.record("SELECT UserID, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)

        if user_id != ctx.author.id:
            return await ctx.send(f"{self.bot.cross} You can't delete others tags. You can only delete your own tags.")

        modified = await self.bot.db.execute(
            "DELETE FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name
        )

        if not modified:
            return await ctx.send(f"{self.bot.cross} That tag does not exist.")

        await ctx.send(f'{self.bot.tick} Tag `{tag_name}` deleted.')


    @tags_group.command(name = "info", help = "Shows information about an existing tag.")
    @commands.bot_has_permissions(send_messages = True)
    async def tag_info_command(self, ctx, tag_name: str):
        if any(c not in ascii_lowercase for c in tag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        tag_names = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)

        if tag_name not in tag_names:
            return await ctx.send(f'{self.bot.cross} The Tag `{tag_name}` does not exist.')

        user_id, tag_id, tag_time = await self.bot.db.record("SELECT UserID, TagID, TagTime FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)

        try:
            user = await self.bot.get_user(user_id)
        except:
            user = await self.bot.fetch_user(user_id)

        embed = discord.Embed(title = 'Tag Info', colour = ctx.author.colour, timestamp = ctx.message.created_at)
        embed.set_thumbnail(url = user.avatar_url)
        embed.add_field(name = "Owner", value = user.mention, inline = False)
        embed.add_field(name = "Tag Name", value = tag_name, inline = True)
        embed.add_field(name = "Tag ID", value = tag_id, inline = True)
        embed.add_field(name = "Created at", value = tag_time, inline = True)
        embed.set_footer(text = f"Requested by {ctx.author.name}", icon_url = ctx.author.avatar_url)

        await ctx.send(embed = embed)


    @tags_group.command(name = "all", help = "Shows the tag list of a tag owner.")
    @commands.bot_has_permissions(send_messages = True)
    async def member_tag_list_command(self, ctx, target: t.Optional[t.Union[discord.Member, converters.User, converters.SearchedMember, str]]):
        target = target or ctx.author
        prefix = await self.bot.prefix(ctx.guild)
        all_tags = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)
        tag_names = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ? AND UserID = ?", ctx.guild.id, target.id)
        tag_all = await self.bot.db.records("SELECT Tagname, TagID FROM tags WHERE GuildID = ? AND UserID = ?", ctx.guild.id, target.id)
        if len(tag_names) == 0:
            if target == ctx.author:
                return await ctx.send(f"{self.bot.cross} You don't have any tag list.")
            else:
                return await ctx.send(f"{self.bot.cross} That member doesn't have any tag list.")
        
        self.user = await self.bot.grab_user(target.id)

        try:
            pagemaps = []

            for tag_name, tag_id in sorted(tag_all):
                content, tag_id = await self.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)
                first_step = discord.utils.escape_markdown(content)
                pagemaps.append(
                    {
                        "header": "Tags",
                        "title": f"All tags of this server for {self.user.name}",
                        "description": f"Using {len(tag_names)} of this server's {len(all_tags)} tags.",
                        "thumbnail":self.user.avatar_url,
                        "fields": (
                            (
                                tag_name,
                                "ID: " + tag_id + "\n\n**Content**" + "\n```\n" + ''.join(first_step.replace('<', '\\<')[0:350]) + "..." + "\n\n```\n***To see this tags whole content type `" + prefix + "tag " + tag_name + "`***",
                                False
                                ),
                            ),
                        }
                    )

            await HelpMenu(ctx, pagemaps).start()

        except IndexError:
            await ctx.send(
                embed=self.bot.embed.build(
                ctx=ctx,
                header="Tags",
                title=f"All tags of this server for {self.user.name}",
                description=f"Using {len(tag_names)} of this server's {len(all_tags)} tags.",
                thumbnail=self.user.avatar_url,
                fields=((tag_name, f"ID: {tag_id}", True) for tag_name, tag_id in sorted(tag_all)),
            )
        )
  

    @tags_group.command(name = "raw", help = "Gets the raw content of the tag.This is with markdown escaped. Useful for editing.", pass_context=True)
    @commands.bot_has_permissions(send_messages = True)
    async def raw_command(self, ctx, tag_name: str):
        if any(c not in ascii_lowercase for c in tag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        tag_content = await self.bot.db.column("SELECT TagContent FROM tags WHERE GuildID = ?", ctx.guild.id)
        tag_names = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)

        if tag_name not in tag_names:
            return await ctx.send(f'{self.bot.cross} The Tag `{tag_name}` does not exist.')

        content, tag_id = await self.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)

        first_step = discord.utils.escape_markdown(content)
        await ctx.send(first_step.replace('<', '\\<'))

        
    @tags_group.command(
        name="list",
        help="Lists the server's tags.",
    )
    @commands.bot_has_permissions(send_messages = True)
    async def tags_list_command(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        tag_names = await self.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.guild.id)
        records = await self.bot.db.records("SELECT TagName, TagID FROM tags WHERE GuildID = ?", ctx.guild.id)

        try:
            pagemaps = []

            for tag_name, tag_id in sorted(records):
                content, tag_id = await self.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.guild.id, tag_name)
                first_step = discord.utils.escape_markdown(content)
                pagemaps.append(
                    {
                        "header": "Tags",
                        "title": f"All tags of this server",
                        "description": f"A total of {len(tag_names)} tags of this server.",
                        "thumbnail": ctx.guild.icon_url,
                        "fields": (
                            (
                                tag_name,
                                "ID: " + tag_id + "\n\n**Content**" + "\n```\n" + ''.join(first_step.replace('<', '\\<')[0:350]) + "..." + "\n\n```\n***To see this tags whole content type `" + prefix + "tag " + tag_name + "`***",
                                False
                                ),
                            ),
                        }
                    )

            await HelpMenu(ctx, pagemaps).start()

        except IndexError:
            await ctx.send(
                embed=self.bot.embed.build(
                ctx=ctx,
                header="Tags",
                title="All tags of this server",
                description=f"A total of {len(tag_names)} tags of this server.",
                thumbnail=ctx.guild.icon_url,
                fields=((tag_name, f"ID: {tag_id}", True) for tag_name, tag_id in sorted(records)),
            )
        )


    @commands.command(name = "stag", help = "Shows the content of an existing global tag.")
    @commands.bot_has_permissions(send_messages = True)
    async def stag_command(self, ctx, stag_name: str):
        if any(c not in ascii_lowercase for c in stag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        stag_content = await self.bot.db.column("SELECT STagContent FROM stags")
        stag_names= await self.bot.db.column("SELECT STagName FROM stags")

        cache = []

        if stag_name not in stag_names:
            await ctx.send(f'{self.bot.cross} The S-Tag `{stag_name}` does not exist.')
            for x in range(len(stag_names)):
                if stag_names[x][0] == stag_name[0]:
                    cache.append(stag_names[x])
                    return await ctx.send("Did you mean..." + '\n'.join(cache))

        else:
        	scontent, stag_id = await self.bot.db.record("SELECT STagContent, STagID FROM stags WHERE STagName = ?", stag_name)

        	await ctx.send(scontent)


    @commands.group(
        name="stags",
        invoke_without_command=True,
        help="Commands to create global tags.",
        )
    @commands.bot_has_permissions(send_messages = True)
    async def stags_group(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        cmds = tuple(sorted(self.bot.get_command("stags").commands, key=lambda c: c.name))

        await ctx.send(
            embed=self.bot.embed.build(
                ctx=ctx,
                header="S-Tags",
                thumbnail=self.bot.user.avatar_url,
                description="There are a few different global tag methods you can use.",
                fields=(
                    *(
                        (
                            cmd.name.title(),
                            f"{cmd.help} For more infomation, use `{prefix}help stags {cmd.name}`",
                            False,
                        )
                        for cmd in cmds
                    ),
                ),
            )
        )


    @stags_group.command(name = "new", help = "Creates a new global tag.")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages = True)
    async def stag_create(self, ctx, stag_name: str, *, scontent):
        if any(c not in ascii_lowercase for c in stag_name):
            return await ctx.send(f"{self.bot.cross} S-Tag identifiers can only contain lower case letters.")

        if len(stag_name) > MAX_TAGNAME_LENGTH:
            return await ctx.send(
                f"{self.bot.cross} S-Tag identifiers must not exceed `{MAX_TAGNAME_LENGTH}` characters in length."
            )

        stag_names = await self.bot.db.column("SELECT STagName FROM stags")

        #if len(tag_names) == MAX_TAGS:
            #return await ctx.send(f"{self.bot.cross} You can only set up to {MAX_TAGS} warn types.")

        if stag_name in stag_names:
            prefix = await self.bot.prefix(ctx.guild)
            return await ctx.send(
                f"{self.bot.cross} That s-tag already exists. You can use `{prefix}stags edit {stag_name}`"
            )

        await self.bot.db.execute(
            "INSERT INTO stags (UserID, STagID, STagName, STagContent) VALUES (?, ?, ?, ?)",
            ctx.author.id,
            self.bot.generate_id(),
            stag_name,
            scontent
        )
        await ctx.send(f'{self.bot.tick} The s-tag `{stag_name}` has been created.')


    @stags_group.command(
        name="edit",
        help="Edits an existing global tag.",
    )
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages = True)
    async def stag_edit(self, ctx, stag_name: str, *, scontent):
        if any(c not in ascii_lowercase for c in stag_name):
            return await ctx.send(f"{self.bot.cross} S-Tag identifiers can only contain lower case letters.")

        user_id, stag_id = await self.bot.db.record("SELECT UserID, STagID FROM stags WHERE STagName = ?", stag_name)

        if user_id != ctx.author.id:
            return await ctx.send(f"{self.bot.cross} You can't edit others s-tags. You can only edit your own s-tags.")

        else:
            stag_content = await self.bot.db.column("SELECT STagContent FROM stags")
            stag_names = await self.bot.db.column("SELECT STagName FROM stags")

            if stag_name not in stag_names:
                return await ctx.send(f'{self.bot.cross} The s-tag `{stag_name}` does not exist.')

            if scontent in stag_content:
                return await ctx.send(f'{self.bot.cross} That content already exists in this `{stag_name}` s-tag.')

            await self.bot.db.execute(
                "UPDATE stags SET STagContent = ? WHERE STagName = ?",
                scontent,
                stag_name,
            )

            await ctx.send(
                f"{self.bot.tick} The `{stag_name}` s-tag's content has been updated."
            )


    @stags_group.command(
        name="delete",
        aliases=["del"],
        help="Deletes an existing global tag.",
    )
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages = True)
    async def stag_delete_command(self, ctx, stag_name: str):
        if any(c not in ascii_lowercase for c in stag_name):
            return await ctx.send(f"{self.bot.cross} S-Tag identifiers can only contain lower case letters.")

        user_id, stag_id = await self.bot.db.record("SELECT UserID, STagID FROM stags WHERE STagName = ?", stag_name)

        if user_id != ctx.author.id:
            return await ctx.send(f"{self.bot.cross} You can't delete others s-tags. You can only delete your own s-tags.")

        modified = await self.bot.db.execute(
            "DELETE FROM stags WHERE STagName = ?", stag_name
        )

        if not modified:
            return await ctx.send(f"{self.bot.cross} That s-tag does not exist.")

        await ctx.send(f'{self.bot.tick} S-Tag `{stag_name}` deleted.')


    @stags_group.command(name = "info", help = "Shows information about an existing global tag.")
    @commands.bot_has_permissions(send_messages = True)
    async def stag_info_command(self, ctx, stag_name: str):
        if any(c not in ascii_lowercase for c in stag_name):
            return await ctx.send(f"{self.bot.cross} S-Tag identifiers can only contain lower case letters.")

        stag_names = await self.bot.db.column("SELECT STagName FROM stags")

        if stag_name not in stag_names:
            return await ctx.send(f'{self.bot.cross} The S-Tag `{stag_name}` does not exist.')

        user_id, stag_id, stag_time = await self.bot.db.record("SELECT UserID, STagID, STagTime FROM stags WHERE STagName = ?", stag_name)

        try:
            user = await self.bot.get_user(user_id)
        except:
            user = await self.bot.fetch_user(user_id)

        embed = discord.Embed(title = 'S-Tag Info', colour = ctx.author.colour, timestamp = ctx.message.created_at)
        embed.set_thumbnail(url = user.avatar_url)
        embed.add_field(name = "Owner", value = user.mention, inline = False)
        embed.add_field(name = "S-Tag Name", value = stag_name, inline = True)
        embed.add_field(name = "S-Tag ID", value = stag_id, inline = True)
        embed.add_field(name = "Created at", value = stag_time, inline = True)
        embed.set_footer(text = f"Requested by {ctx.author.name}", icon_url = ctx.author.avatar_url)

        await ctx.send(embed = embed)


    @stags_group.command(name = "all", help = "Shows the global tag list of a global tag owner.")
    @commands.bot_has_permissions(send_messages = True)
    async def member_stag_list_command(self, ctx, target: t.Optional[t.Union[discord.Member, converters.User, converters.SearchedMember, str]]):
        target = target or ctx.author
        prefix = await self.bot.prefix(ctx.guild)
        all_stags = await self.bot.db.column("SELECT STagName FROM stags")
        stag_names = await self.bot.db.column("SELECT STagName FROM stags WHERE UserID = ?", target.id)
        stag_all = await self.bot.db.records("SELECT STagname, STagID FROM stags WHERE UserID = ?", target.id)
        if len(stag_names) == 0:
            if target == ctx.author:
                return await ctx.send(f"{self.bot.cross} You don't have any s-tag list.")
            else:
                return await ctx.send(f"{self.bot.cross} That member doesn't have any s-tag list.")
       
        self.user = await self.bot.grab_user(target.id)

        try:
            pagemaps = []

            for stag_name, stag_id in sorted(stag_all):
                scontent, stag_id = await self.bot.db.record("SELECT STagContent, STagID FROM stags WHERE STagName = ?", stag_name)
                first_step = discord.utils.escape_markdown(scontent)
                pagemaps.append(
                    {
                        "header": "S-Tags",
                        "title": f"All tags within the globe for {self.user.name}",
                        "description": f"Using {len(stag_names)} of the globe's {len(all_stags)} tags.",
                        "thumbnail":self.user.avatar_url,
                        "fields": (
                            (
                                stag_name,
                                "ID: " + stag_id + "\n\n**Content**" + "\n```\n" + ''.join(first_step.replace('<', '\\<')[0:350]) + "..." + "\n\n```\n***To see this s-tags whole content type `" + prefix + "stag " + stag_name + "`***",
                                False
                                ),
                            ),
                        }
                    )

            await HelpMenu(ctx, pagemaps).start()

        except IndexError:
            await ctx.send(
                embed=self.bot.embed.build(
                ctx=ctx,
                header="S-Tags",
                title=f"All tags within the globe for {self.user.name}",
                description=f"Using {len(stag_names)} of the globe's {len(all_stags)} stags.",
                thumbnail=self.user.avatar_url,
                fields=((stag_name, f"ID: {stag_id}", True) for stag_name, stag_id in sorted(stag_all)),
            )
        )
  

    @stags_group.command(name = "raw", help = "Gets the raw content of the global tag. This is with markdown escaped. Useful for editing.")
    @commands.bot_has_permissions(send_messages = True)
    async def sraw_command(self, ctx, stag_name: str):
        if any(c not in ascii_lowercase for c in stag_name):
            return await ctx.send(f"{self.bot.cross} Tag identifiers can only contain lower case letters.")

        stag_content = await self.bot.db.column("SELECT STagContent FROM stags")
        stag_names = await self.bot.db.column("SELECT STagName FROM stags")

        if stag_name not in stag_names:
            return await ctx.send(f'{self.bot.cross} The S-Tag `{stag_name}` does not exist.')

        scontent, stag_id = await self.bot.db.record("SELECT STagContent, STagID FROM stags WHERE STagName = ?", stag_name)

        first_step = discord.utils.escape_markdown(scontent)
        await ctx.send(first_step.replace('<', '\\<'))

        
    @stags_group.command(
        name="list",
        help="Lists the global tags.",
    )
    @commands.bot_has_permissions(send_messages = True)
    async def stags_list_command(self, ctx):
        prefix = await self.bot.prefix(ctx.guild)
        stag_names = await self.bot.db.column("SELECT STagName FROM stags")
        records = await self.bot.db.records("SELECT STagName, STagID FROM stags")

        try:
            pagemaps = []

            for stag_name, stag_id in sorted(records):
                scontent, stag_id = await self.bot.db.record("SELECT STagContent, STagID FROM stags WHERE STagName = ?", stag_name)
                first_step = discord.utils.escape_markdown(scontent)
                pagemaps.append(
                    {
                        "header": "S-Tags",
                        "title": f"All tags within the globe",
                        "description": f"A total of {len(stag_names)} tags within the globe.",
                        "thumbnail": ctx.guild.icon_url,
                        "fields": (
                            (
                                stag_name,
                                "ID: " + stag_id + "\n\n**Content**" + "\n```\n" + ''.join(first_step.replace('<', '\\<')[0:350]) + "..." + "\n\n```\n***To see this s-tags whole content type `" + prefix + "stag " + stag_name + "`***",
                                False
                                ),
                            ),
                        }
                    )

            await HelpMenu(ctx, pagemaps).start()

        except IndexError:
            await ctx.send(
                embed=self.bot.embed.build(
                ctx=ctx,
                header="S-Tags",
                title="All tags within the globe",
                description=f"A total of {len(stag_names)} tags within the globe.",
                thumbnail=ctx.guild.icon_url,
                fields=((stag_name, f"ID: {stag_id}", True) for stag_name, stag_id in sorted(records)),
            )
        )
            

def setup(bot):
    bot.add_cog(Tags(bot))
