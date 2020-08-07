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

from collections import deque

from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType

ACTIVITY_TYPES = ("playing", "watching", "listening", "streaming")


class PresenceSetter:
    def __init__(self, bot):
        self.bot = bot

        self._name = "@S4 help • {message} • Version {version}"
        self._type = "watching"
        self._messages = deque(
            (
                "Invite S4 to your server by using @S4 invite",
                "To view information about S4, use @S4 botinfo",
                "Need help with S4? Join the support server! Use @S4 support to get an invite",
                "Developed by Parafoxia#1911 under the MPL-2.0 license",
            )
        )

        self.bot.scheduler.add_job(self.set, CronTrigger(second=0))

    @property
    def name(self):
        message = self._messages[0].format(bot=self.bot)
        return self._name.format(message=message, version=self.bot.version)

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def type(self):
        return getattr(ActivityType, self._type, ActivityType.playing)

    @type.setter
    def type(self, value):
        if value not in ACTIVITY_TYPES:
            raise ValueError("The activity should be one of the following: {}".format(", ".join(ACTIVITY_TYPES)))

        self._type = value

    async def set(self):
        await self.bot.change_presence(activity=Activity(name=self.name, type=self.type))
        self._messages.rotate(-1)
