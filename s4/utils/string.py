from string import Formatter

ORDINAL_ENDINGS = {"1": "st", "2": "nd", "3": "rd"}


class MessageFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                return key
        else:
            return super().get_value(key, args, kwargs)


def safe_format(text, *args, **kwargs):
    formatter = Formatter()
    return formatter.format(text, *args, **kwargs)


def text_is_formattible(text):
    try:
        return safe_format(text)
    except:
        return False


def list_of(items):
    if len(items) > 2:
        return "{}, and {}".format(", ".join(items[:-1]), items[-1])
    else:
        return " and ".join(items)


def ordinal(number):
    if str(number)[-2:] not in ("11", "12", "13"):
        return f"{number:,}{ORDINAL_ENDINGS.get(str(number)[-1], 'th')}"
    else:
        return f"{number:,}th"
