#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
#    Copyright (C) 2017, Kai Raphahn <kai.raphahn@laburec.de>
#

import subprocess
import os
import platform
import json
import struct

__all__ = [
    "check_dict",
    "check_object",
    "openjson",
    "full_path",
    "get_attribute",
    "get_terminal_size",
    "print_exception",
    "execute"
]


def check_dict(checkdict: dict, keylist: list) -> bool:
    ret = True
    list_keys = list(checkdict)

    for key in keylist:
        if list_keys.count(key) == 0:
            ret = False

    return ret


def check_object(checkobject, keylist: list) -> bool:
    ret = True

    if checkobject is None:
        return False

    for key in keylist:
        if hasattr(checkobject, key) is False:
            ret = False

    return ret


def openjson(filename: str):
    f = open(filename, mode='r', encoding="utf-8")
    data = json.load(f)
    f.close()
    return data


def full_path(pathname: str) -> str:
    filename = os.path.abspath(os.path.normpath(pathname))
    return filename


def get_attribute(path: str, classname: str):
    fromlist = [classname]

    try:
        m = __import__(path, globals(), locals(), fromlist)
    except ImportError:
        raise ImportError("Unable to find module path: {0:s}".format(path))

    try:
        c = getattr(m, classname)
    except AttributeError:
        raise ImportError("Unable to get module attribute: {0:s} with {1:s}".format(path, classname))

    return c


def _get_terminal_size_windows():  # pragma: no cover
    try:
        import struct
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh",
                                                                                                  csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except Exception as e:
        print("Unable to get terminal size!")
        print(str(e))
        pass
    return 80, 25


def _get_terminal_size_tput():  # pragma: no cover
    """get terminal width
    src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    """
    try:
        import subprocess
        import shlex
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        ret = (cols, rows)
        return ret
    except Exception as e:
        print_exception(e)
    return 80, 25


# noinspection PyUnresolvedReferences
def _ioctl_gwinsz(fdin):
    import fcntl
    import termios
    cr_data = None

    try:
        cr_data = struct.unpack('hh', fcntl.ioctl(fdin, termios.TIOCGWINSZ, '1234'))
    except Exception as ex:
        print_exception(ex)

    return cr_data


def _get_terminal_size_linux():  # pragma: no cover
    cr = _ioctl_gwinsz(0) or _ioctl_gwinsz(1) or _ioctl_gwinsz(2)
    if not cr:

        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = _ioctl_gwinsz(fd)
            os.close(fd)
        except Exception as ex:
            print_exception(ex)

    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except Exception as ex:
            print_exception(ex)
            return 80, 25

    return int(cr[1]), int(cr[0])


def get_terminal_size():  # pragma: no cover
    current_os = platform.system()
    tuple_xy = (80, 40)
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()

        # needed for window's python in cygwin's xterm!
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()

    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()

    # default value
    if tuple_xy is None:
        tuple_xy = (0, 0)
    return tuple_xy


def print_exception(e: Exception):
    message1 = "An exception of type {0:s} occurred.".format(type(e).__name__)
    message2 = "Arguments:\n{0!r}".format(e.args)
    print(message1)
    print(message2)
    return


def execute(name: str, command: list, data: list = None, callback=None):
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as e:
        if callback is not None:
            callback.exception(e)
            callback.traceback()
        return False, 0

    for _line in proc.stdout:
        line = _line.decode('utf-8')

        line = line.replace("\r\n", "")
        line = line.replace("\n", "")

        if data is not None:
            data.append(line)

        if callback is None:
            continue

        callback.inform(name, line)

    proc.wait()

    returncode = proc.returncode

    if callback is not None:
        callback.inform(name, str(proc.returncode))

    return True, returncode
