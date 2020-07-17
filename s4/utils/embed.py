from datetime import datetime

from discord import Embed

from s4.utils import DEFAULT_EMBED_COLOUR, EMBEDS


class EmbedConstructor:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_pagemap(key):
        return EMBEDS.get(key, {})

    def build(self, **kwargs):
        ctx = kwargs.get("ctx")

        embed = Embed(
            title=kwargs.get("title"),
            description=kwargs.get("description"),
            colour=(
                kwargs.get("colour") or ctx.author.colour
                if ctx and ctx.author.colour.value
                else None or DEFAULT_EMBED_COLOUR
            ),
            timestamp=datetime.utcnow(),
        )

        embed.set_author(name=kwargs.get("header", "S4"))
        embed.set_footer(
            text=kwargs.get(
                "footer", f"Requested by {ctx.author.display_name}" if ctx else "Server Safety and Security Systems"
            ),
            icon_url=ctx.author.avatar_url if ctx else Embed.Empty,
        )

        # FIXME: In d.py 1.4, `Embed.Empty` will be supported.
        if thumbnail := kwargs.get("thumbnail"):
            embed.set_thumbnail(url=thumbnail)

        # FIXME: In d.py 1.4, `Embed.Empty` will be supported.
        if image := kwargs.get("image"):
            embed.set_image(url=image)

        for name, value, inline in kwargs.get("fields", []):
            embed.add_field(name=name, value=value, inline=inline)

        return embed

    def load(self, key, **kwargs):
        pagemap = self.get_pagemap(key)
        ctx = kwargs.get("ctx")

        embed = Embed(
            title=kwargs.get("title", pagemap.get("title", "")).format(**kwargs),
            description=kwargs.get("description", pagemap.get("description", "")).format(**kwargs),
            colour=(
                # The pagemap colour must be an integer, not hex.
                pagemap.get("colour") or ctx.author.colour
                if ctx and ctx.author.colour.value
                else None or DEFAULT_EMBED_COLOUR
            ),
            timestamp=datetime.utcnow(),
        )

        embed.set_author(name=pagemap.get("header", "S4"))
        embed.set_footer(
            text=pagemap.get(
                "footer", f"Invoked by {ctx.author.display_name}" if ctx else "Server Safety and Security Systems"
            ).format(**kwargs),
            icon_url=ctx.author.avatar_url if ctx else Embed.Empty,
        )

        # NOTE: Thumbails and images still need to passed through as kwargs.
        # FIXME: In d.py 1.4, `Embed.Empty` will be supported.
        if thumbnail := kwargs.get("thumbnail"):
            embed.set_thumbnail(url=thumbnail)

        # FIXME: In d.py 1.4, `Embed.Empty` will be supported.
        if image := kwargs.get("image"):
            embed.set_image(url=image)

        for name, value, inline in pagemap.get("fields", kwargs.get("fields", [])):
            embed.add_field(name=name.format(**kwargs), value=value.format(**kwargs), inline=inline)

        return embed
