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

import os
import subprocess as sp

from s4.utils import ROOT_DIR


def _loc(filetype):
    if os.name == "nt":
        return int(
            sp.check_output(
                [
                    "powershell.exe",
                    f"(Get-ChildItem -Path \"{ROOT_DIR / 's4'}\" | Get-ChildItem -Filter '*.{filetype}' -Recurse | Get-Content | Measure-Object -line).lines",
                ]
            )
        )
    # FIXME: This just doesn't work.
    # elif os.name == "posix":
    #     return int(
    #         sp.check_output(f"find {ROOT_DIR / 's4'} -type f -name \"*.{filetype}\" -print0 | wc -l --files0-from=-")
    #     )
    return 0


def python_lines():
    return _loc("py")


def json_lines():
    return _loc("json")


def sql_lines():
    return _loc("sql")
