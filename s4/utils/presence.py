from collections import deque

from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType


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

    async def set(self):
        await self.bot.change_presence(activity=Activity(name=self.name, type=self.type))
        self._messages.rotate(-1)
