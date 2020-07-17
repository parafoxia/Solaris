from pathlib import Path

from toml import loads

from s4.config import Config

# Dependant on above imports.
from s4.bot import Bot

__version__ = loads(open(Path(__name__).resolve().parents[0] / "pyproject.toml").read())["tool"]["poetry"]["version"]
