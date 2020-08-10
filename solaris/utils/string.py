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
