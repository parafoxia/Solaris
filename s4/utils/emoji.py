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

from discord import utils

# If S4 can't use the correct emojis, fall back to these.
ALTERNATIVES = {
    "confirm": "✅",
    "cancel": "❎",
    "exit": "⏏️",
    "info": "ℹ️",
    "loading": "⏱️",
    "option1": "1️⃣",
    "option2": "2⃣",
    "option3": "3⃣",
    "option4": "4⃣",
    "option5": "5⃣",
    "option6": "6⃣",
    "option7": "7⃣",
    "option8": "8⃣",
    "option9": "9⃣",
    "pageback": "◀️",
    "pagenext": "▶️",
    "stepback": "⏪",
    "stepnext": "⏩",
}


class EmojiGetter:
    def __init__(self, bot):
        self.bot = bot

    def get(self, name):
        hub = self.bot.get_cog("Hub")

        if getattr(hub, "guild", None) is not None:
            return utils.get(hub.guild.emojis, name=name) or ALTERNATIVES[name]
        else:
            return ALTERNATIVES[name]

    def get_many(self, *names):
        hub = self.bot.get_cog("Hub")

        if getattr(hub, "guild", None) is not None:
            return [utils.get(hub.guild.emojis, name=name) or ALTERNATIVES[name] for name in names]
        else:
            return [ALTERNATIVES[name]]

    def yield_many(self, *names):
        hub = self.bot.get_cog("Hub")

        if getattr(hub, "guild", None) is not None:
            for name in names:
                yield utils.get(hub.guild.emojis, name=name) or ALTERNATIVES[name]
        else:
            yield ALTERNATIVES[name]

    def mention(self, name):
        hub = self.bot.get_cog("Hub")

        if getattr(hub, "guild", None) is not None:
            return f"{utils.get(hub.guild.emojis, name=name) or ALTERNATIVES[name] or ''}"
        else:
            return ALTERNATIVES[name] or ""
