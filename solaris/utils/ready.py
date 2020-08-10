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

# Ethan Henderson
# parafoxia@carberra.xyz


class Ready:
    def __init__(self, bot):
        self.bot = bot
        self.booted = False
        self.synced = False

        for cog in self.bot._cogs:
            setattr(self, cog, False)

    def up(self, cog):
        setattr(self, qn := cog.qualified_name.lower(), True)
        print(f" `{qn}` cog ready.")

    @property
    def ok(self):
        return self.booted and all(getattr(self, cog) for cog in self.bot._cogs)

    @property
    def initialised_cogs(self):
        return [cog for cog in self.bot._cogs if getattr(self, cog)]

    def __str__(self):
        string = "Bot is booted." if self.booted else "Bot is not booted."
        string += f" {len(self.initialised_cogs)} of {len(self.bot._cogs)} cogs initialised."
        return string

    def __repr__(self):
        return f"<Ready booted={self.booted!r} ok={self.ok!r}>"

    def __int__(self):
        return len(self.initialised_cogs)

    def __bool__(self):
        return self.ok
