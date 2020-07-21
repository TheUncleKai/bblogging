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

import os

from datetime import datetime

from bbutil.logging.types import Writer, Message
from bbutil.utils import full_path, print_exception

__all__ = [
    "FileWriter"
]

_index = ["INFORM", "DEBUG1", "DEBUG2", "DEBUG3", "WARN", "ERROR", "EXCEPTION", "TIMER"]

classname = "FileWriter"


class FileWriter(Writer):

    def __init__(self):
        Writer.__init__(self, "File", _index)

        self.filename = ""
        self.append_data = False
        self.text_space = 15

        # noinspection PyTypeChecker
        self.file = None
        return

    def setup(self, **kwargs):
        logname = ""
        append_datetime = False
        logpath = ""

        item = kwargs.get("text_space", None)
        if item is not None:
            self.text_space = item

        item = kwargs.get("filename", None)
        if item is not None:
            self.filename = full_path(item)

        item = kwargs.get("logname", None)
        if item is not None:
            logname = item

        item = kwargs.get("logpath", None)
        if item is not None:
            logpath = item

        item = kwargs.get("append_datetime", None)
        if item is not None:
            append_datetime = item

        item = kwargs.get("append_data", None)
        if item is not None:
            self.append_data = item

        if (append_datetime is True) and ((logname == "") or (logpath == "")):
            raise ValueError("For appending datetime these values have to been set: append_datetime, logname, logpath")

        if (append_datetime is True) and (logname != "") and (logpath != ""):
            timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
            path = "{0:s}/{1:s}_{2:s}.log".format(logpath, logname, timestamp)
            self.filename = os.path.normpath(path)
        return

    def clear(self) -> bool:
        return True

    def open(self) -> bool:

        if self.filename == "":
            raise ValueError("Filename is missing!")

        if self.append_data is True:
            mode = 'ab'
        else:
            mode = 'wb'

        try:
            self.file = open(self.filename, mode)
        except ValueError as e:
            line = "Filename: {0:s}\nMode: {1:s}".format(self.filename, mode)
            print(line)
            print_exception(e)
            return False
        except OSError as e:
            print_exception(e)
            return False

        return True

    def close(self) -> bool:
        if self.file is not None:
            self.file.close()
            self.file = None
        return True

    def _write_raw(self, item: Message):
        if self.file is None:
            raise ValueError("File is not open!")

        data = item.content.encode('latin-1', 'ignore')

        try:
            self.file.write(data)
            self.file.flush()
        except OSError as e:
            print_exception(e)
            return

        return

    def _write_item(self, item: Message):
        if self.file is None:
            raise ValueError("File is not open!")

        timestamp = item.time.strftime('%Y-%m-%d %H:%M:%S ')
        appname = "{0:s}".format(item.app).ljust(self.text_space)

        if item.tag == "":
            line = "{0:s}{1:s} {2:s}: {3:s}\n".format(timestamp, appname, item.level, item.content)
        else:
            line = "{0:s}{1:s} {2:s}: {3:s} - {4:s}\n".format(timestamp, appname, item.level, item.tag, item.content)

        data = line.encode('latin-1', 'ignore')

        try:
            self.file.write(data)
            self.file.flush()
        except OSError as e:
            print_exception(e)
        return

    def write(self, item: Message):
        if item.raw is True:
            self._write_raw(item)
        else:
            self._write_item(item)
        return
