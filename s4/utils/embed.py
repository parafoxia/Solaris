from datetime import datetime

from discord import Embed

from s4.utils import DEFAULT_EMBED_COLOUR, EMBEDS


class EmbedConstructor:
    def __init__(self, bot):
        self.bot = bot

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
        stored = EMBEDS[key]
        ctx = kwargs.get("ctx")

        embed = Embed(
            title=stored.get("title"),
            description=stored.get("description"),
            colour=(
                # The stored colour must be an integer, not hex.
                stored.get("colour") or ctx.author.colour
                if ctx and ctx.author.colour.value
                else None or DEFAULT_EMBED_COLOUR
            ),
            timestamp=datetime.utcnow(),
        )

        embed.set_author(name=stored.get("header", "S4"))
        embed.set_footer(
            text=stored.get(
                "footer", f"Requested by {ctx.author.display_name}" if ctx else "Server Safety and Security Systems"
            ),
            icon_url=ctx.author.avatar_url if ctx else Embed.Empty,
        )

        # NOTE: Thumbails and images still need to passed through as kwargs.
        # FIXME: In d.py 1.4, `Embed.Empty` will be supported.
        if thumbnail := kwargs.get("thumbnail"):
            embed.set_thumbnail(url=thumbnail)

        # FIXME: In d.py 1.4, `Embed.Empty` will be supported.
        if image := kwargs.get("image"):
            embed.set_image(url=image)

        for name, value, inline in stored.get("fields", kwargs.get("fields", [])):
            embed.add_field(name=name, value=value, inline=inline)

        return embed