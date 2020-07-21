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

import sys
import colorama
import platform

from bbutil.logging.types import Writer, Message
from bbutil.utils import get_terminal_size

__all__ = [
    "ConsoleWriter"
]

colorama.init()

classname = "ConsoleWriter"
RESET_ALL = colorama.Style.RESET_ALL


class _Style(object):

    def __init__(self, name: str, text: str, foreground: str, background: str):
        self.name = name
        self.text = text
        self.foreground = foreground
        self.background = background
        return

    @property
    def scheme(self) -> str:
        scheme = ""

        scheme += self._get_colorama(colorama.Style, self.text)
        scheme += self._get_colorama(colorama.Fore, self.foreground)
        scheme += self._get_colorama(colorama.Back, self.background)
        return scheme

    @staticmethod
    def _get_colorama(attribute, name):
        try:
            ret = getattr(attribute, name)
        except AttributeError:
            ret = ""

        return ret


_index = ["INFORM", "DEBUG1", "DEBUG2", "DEBUG3", "WARN", "ERROR", "EXCEPTION", "TIMER", "PROGRESS"]

_schemes = {
    "INFORM": _Style("INFORM", "BRIGHT", "GREEN", ""),
    "DEBUG1": _Style("DEBUG1", "", "WHITE", "BLACK"),
    "DEBUG2": _Style("DEBUG2", "DIM", "CYAN", "BLACK"),
    "DEBUG3": _Style("DEBUG3", "BRIGHT", "BLACK", "BLACK"),
    "WARN": _Style("INFORM", "BRIGHT", "MAGENTA", ""),
    "ERROR": _Style("ERROR", "BRIGHT", "RED", ""),
    "EXCEPTION": _Style("EXCEPTION", "BRIGHT", "RED", ""),
    "TIMER": _Style("TIMER", "BRIGHT", "YELLOW", "")
}


class ConsoleWriter(Writer):

    def __init__(self):
        Writer.__init__(self, "Console", _index)

        self.styles = _schemes
        self.encoding = ""
        self.text_space = 15
        self.seperator = "|"
        self.length = 0
        self.error_index = ["ERROR", "EXCEPTION"]
        self.use_error = False
        self.stdout = sys.stdout
        self.stderr = sys.stderr

        size_x, size_y = get_terminal_size()

        self.line_width = size_x
        self.bar_len = 50
        return

    def setup(self, **kwargs):
        item = kwargs.get("text_space", None)
        if item is not None:
            self.text_space = item

        item = kwargs.get("seperator", None)
        if item is not None:
            self.seperator = item

        item = kwargs.get("error_index", None)
        if item is not None:
            self.error_index = item

        item = kwargs.get("bar_len", None)
        if item is not None:
            self.bar_len = item
        return

    def add_style(self, name: str, text: str, foreground: str, background: str):
        style = _Style(name, text, foreground, background)
        self.styles[style.name] = style
        return

    def open(self) -> bool:
        self.encoding = self.stdout.encoding
        os_name = platform.system()
        if self.encoding is None:  # pragma: no cover
            if os_name == "Windows":
                self.encoding = "cp850"

        return True

    def close(self) -> bool:  # pragma: no cover
        return True

    def clear(self) -> bool:
        filler = ' ' * self.length
        content = "\r{0:s}\r".format(filler)

        if self.use_error is True:
            self.stderr.write(content)
        else:
            self.stdout.write(content)
        return True

    def write(self, item: Message):
        error = False

        if item.level in self.error_index:
            error = True

        if item.level == "PROGRESS":
            self._write_progress(item)
            return

        if item.raw is True:
            self._write(error, item.content, "Unable to log content due de- or encoding error!")
        else:
            content = self._create_color(item, item.content)
            fallback = self._create_color(item, "Unable to log content due de- or encoding error!")
            self._write(error, content, fallback)
        return

    def _write_progress(self, item: Message):
        self.use_error = False
        value = self.bar_len * item.progress.counter / float(item.progress.limit)

        filled_len = int(round(value))

        bars = '=' * filled_len
        filler = '-' * (self.bar_len - filled_len)

        percents = "{0:.1f}%".format(round(item.progress.value, 1)).rjust(6, ' ')

        limit = 3 + (item.progress.length * 2)
        counter = "({0:d}/{1:d})".format(item.progress.counter, item.progress.limit).rjust(limit)

        content = " [{0:s}{1:s}] {2:s} {3:s}".format(bars, filler, percents, counter)

        if len(content) > self.line_width:
            return

        self.length = len(content) + 1

        try:
            output = content.encode(self.encoding, "replace").decode(self.encoding, "replace")
        except UnicodeDecodeError:  # pragma: no cover
            return

        line = '\r' + output
        self.stdout.write(line)
        return

    def _create_color(self, item: Message, text: str) -> str:
        appname = "{0:s} ".format(item.app).ljust(self.text_space)
        scheme = self.styles[item.level].scheme

        if item.tag == "":
            content = "{0:s}{1:s}{2:s} {3:s}{4:s}".format(RESET_ALL, appname, scheme, text, RESET_ALL)
        else:
            tag = item.tag.ljust(self.text_space)
            content = "{0:s}{1:s}{2:s} {3:s}{4:s} {5:s}{6:s}".format(RESET_ALL, appname, scheme, tag, self.seperator,
                                                                     RESET_ALL, text)
        return content

    def _write(self, error: bool, content: str, fallback: str):
        output = ""

        try:
            output += content.encode(self.encoding, "replace").decode(self.encoding, "replace")
            self.data = output

        except UnicodeDecodeError as e:  # pragma: no cover
            output += "UnicodeDecodeError: " + str(e) + "\n"
            output += fallback + "\n"

        except UnicodeEncodeError as e:  # pragma: no cover
            output += "UnicodeEncodeError: " + str(e) + "\n"
            output += fallback + "\n"

        # Now we write the output to the console
        output += '\n'

        self.length = len(output)

        if error is True:
            self.use_error = True
            self.stderr.write(output)
        else:
            self.use_error = False
            self.stdout.write(output)
        return
