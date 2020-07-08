from os import getenv
from typing import Final

from dotenv import load_dotenv

load_dotenv()


class Config:
    try:
        # Load production token.
        with open(getenv("TOKEN", "")) as f:
            token = f.read()
    except FileNotFoundError:
        # Load development token.
        token = getenv("TOKEN", "")

    TOKEN: Final = token
    DEFAULT_PREFIX: Final = getenv("DEFAULT_PREFIX", ">>")
    HUB_GUILD_ID: Final = int(getenv("HUB_GUILD_ID", ""))
    HUB_COMMANDS_CHANNEL_ID: Final = int(getenv("HUB_COMMANDS_CHANNEL_ID", ""))
    HUB_RELAY_CHANNEL_ID: Final = int(getenv("HUB_RELAY_CHANNEL_ID", ""))
    HUB_STDOUT_CHANNEL_ID: Final = int(getenv("HUB_STDOUT_CHANNEL_ID", ""))
