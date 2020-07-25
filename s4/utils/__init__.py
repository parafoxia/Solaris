__all__ = [
    "DEFAULT_EMBED_COLOUR",
    "EMBEDS",
    "ERROR_ICON",
    "HELPS",
    "INFO_ICON",
    "LOADING_ICON",
    "MESSAGES",
    "ROOT_DIR",
]

from json import load
from pathlib import Path

DEFAULT_EMBED_COLOUR = 0x38B3C8
ERROR_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/710866387018711080/cancel.png"
INFO_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/711348122915176529/info.png"
LOADING_ICON = "https://cdn.discordapp.com/attachments/710177462989881415/710178153200353360/loading500.gif"
ROOT_DIR = Path(__file__).parent.parent.parent

with open("./s4/data/static/embeds.json", "r", encoding="utf-8") as f:
    EMBEDS = load(f)

with open("./s4/data/static/help.json", "r", encoding="utf-8") as f:
    HELPS = load(f)

# Dependant on constants above.
from .embed import EmbedConstructor
from .emoji import EmojiGetter
from .presence import PresenceSetter
from .ready import Ready
from .search import Search
