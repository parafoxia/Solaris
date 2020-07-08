from s4.utils import MESSAGES

STANDARD_MESSAGES = MESSAGES["standard"]
SUCCESS_MESSAGES = MESSAGES["success"]
INFO_MESSAGES = MESSAGES["info"]
ERROR_MESSAGES = MESSAGES["error"]


class MessageConstructor:
    def __init__(self, bot):
        self.bot = bot

    def send(self, body, kind=None, **kwargs):
        if kind is None:
            return body.format(**kwargs)

        elif kind == "success":
            return f"{self.bot.emoji.mention('confirm')} {body.format(**kwargs)}"

        elif kind == "info":
            return f"{self.bot.emoji.mention('info')} {body.format(**kwargs)}"

        elif kind == "error":
            return f"{self.bot.emoji.mention('cancel')} {body.format(**kwargs)}"

    def load(self, key, **kwargs):
        if key in STANDARD_MESSAGES.keys():
            return STANDARD_MESSAGES[key].format(**kwargs)

        elif key in SUCCESS_MESSAGES.keys():
            return f"{self.bot.emoji.mention('confirm')} {SUCCESS_MESSAGES[key].format(**kwargs)}"

        elif key in INFO_MESSAGES.keys():
            return f"{self.bot.emoji.mention('info')} {INFO_MESSAGES[key].format(**kwargs)}"

        elif key in ERROR_MESSAGES.keys():
            return f"{self.bot.emoji.mention('cancel')} {ERROR_MESSAGES[key].format(**kwargs)}"
