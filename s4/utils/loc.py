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
    elif os.name == "posix":
        return int(
            sp.check_output(f"find {ROOT_DIR / 's4'} -type f -name \"*.{filetype}\" -print0 | wc -l --files0-from=-")
        )
    return 0


def python_lines():
    return _loc("py")


def json_lines():
    return _loc("json")


def sql_lines():
    return _loc("sql")
