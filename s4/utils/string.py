from string import Formatter

ORDINAL_ENDINGS = {"1": "st", "2": "nd", "3": "rd"}


class MessageFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                return "<BAD_VARIABLE>"
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


def list_of(items, sep="and"):
    if len(items) > 2:
        return "{}, {} {}".format(", ".join(items[:-1]), sep, items[-1])
    else:
        return f" {sep} ".join(items)


def ordinal(number):
    if str(number)[-2:] not in ("11", "12", "13"):
        return f"{number:,}{ORDINAL_ENDINGS.get(str(number)[-1], 'th')}"
    else:
        return f"{number:,}th"
