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

__all__ = [
    "DEFAULT_EMBED_COLOUR",
    "ERROR_ICON",
    "HELPS",
    "INFO_ICON",
    "LOADING_ICON",
    "ROOT_DIR",
    "SUCCESS_ICON",
    "SUPPORT_GUILD_INVITE_LINK",
]

from json import load
from pathlib import Path

DEFAULT_EMBED_COLOUR = 0x38B3C8
ERROR_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/710866387018711080/cancel.png"
INFO_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/711348122915176529/info.png"
LOADING_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/710178153200353360/loading500.gif"
ROOT_DIR = Path(__file__).parent.parent.parent
SUCCESS_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/738066048640876544/confirm.png"
SUPPORT_GUILD_INVITE_LINK = "https://discord.gg/c3b4cZs"

# Dependant on constants above.
from .embed import EmbedConstructor
from .emoji import EmojiGetter
from .presence import PresenceSetter
from .ready import Ready
from .search import Search
