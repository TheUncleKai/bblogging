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
import time
import traceback
from threading import Thread

import bbutil.logging.writer

from bbutil.logging.types import Timer, Message, Writer, Progress
from bbutil.utils import get_attribute

__all__ = [
    "writer",
    "types",

    "Logging"
]

_index = {
    0: ["INFORM", "WARN", "ERROR", "EXCEPTION", "TIMER", "PROGRESS"],
    1: ["INFORM", "DEBUG1", "WARN", "ERROR", "EXCEPTION", "TIMER", "PROGRESS"],
    2: ["INFORM", "DEBUG1", "DEBUG1", "WARN", "ERROR", "EXCEPTION", "TIMER", "PROGRESS"],
    3: ["INFORM", "DEBUG1", "DEBUG2", "DEBUG3", "WARN", "ERROR", "EXCEPTION", "TIMER", "PROGRESS"]
}


class LogState(object):

    def __init__(self):
        self.close = False
        self.open = False
        self.use_thread = False
        self.thread_active = False
        return


class Logging(object):

    def __init__(self):
        self._level = 0
        self._app = ""
        self._timer_list = []
        self._timer_counter = 0

        self._buffer = []
        self._interval = 0.01
        self._index = {}
        self._writer = []

        self.state = LogState()
        return

    def __del__(self):
        return

    @staticmethod
    def get_writer(name: str) -> Writer:
        c = None

        for item in bbutil.logging.writer.__all__:

            if item != name:
                continue

            path = "bbutil.logging.writer.{0:s}".format(item)
            classname = get_attribute(path, "classname")
            c = get_attribute(path, classname)

        if c is None:
            raise ImportError("Unable to find writer: {0:s}".format(name))

        _writer = c()
        return _writer

    def _process(self, item: Message):
        for _writer in self._writer:
            if (item.level not in _writer.index) and (item.raw is False):
                continue
            _writer.write(item)
        return

    def _run(self):
        self.state.thread_active = True

        while True:
            item_counter = len(self._buffer)

            self._thread = True

            # only quit when buffer is empty
            if (self.state.close is True) and (item_counter == 0):
                self.state.thread_active = False
                break

            time.sleep(self._interval)
            count = len(self._buffer)

            if count == 0:
                continue

            _message = self._buffer.pop(0)
            self._process(_message)
        return

    def register(self, write: Writer):
        self._writer.append(write)
        return

    def append(self, item: Message):
        if self._level not in self._index:
            return

        level_list = self._index[self._level]

        if (item.level not in level_list) and (item.raw is False):
            return

        item.app = self._app

        # select output method: if threaded use buffer for output, if not print directly
        if self.state.use_thread is True:
            self._buffer.append(item)
        else:
            self._process(item)
        return

    def setup(self, **kwargs):
        item = kwargs.get("app", None)
        if item is not None:
            self._app = item

        item = kwargs.get("interval", None)
        if item is not None:
            self._interval = item

        item = kwargs.get("level", None)
        if item is not None:
            self._level = item

        item = kwargs.get("index", None)
        if item is not None:
            self._index = item

        item = kwargs.get("use_thread", None)
        if item is not None:
            self.state.use_thread = item
        return

    def open(self) -> bool:
        if (self.state.use_thread is True) and (self.state.thread_active is True):
            print("A logging thread is already running!")
            return False

        length = len(self._index)
        if length == 0:
            self._index = _index

        if len(self._writer) == 0:
            print("Not output writer selected!")
            return False

        for item in self._writer:
            check = item.open()
            if check is False:
                return False

        self.state.open = True

        if self.state.use_thread is True:
            thread = Thread(target=self._run)
            thread.start()
        return True

    def _close_thread(self):
        if self.state.use_thread is False:
            return

        # wait for thread to close
        while True:
            if self.state.thread_active is False:
                break
            time.sleep(0.01)
        return

    def close(self) -> bool:
        self.state.close = True

        self._close_thread()
        for item in self._writer:
            check = item.close()
            if check is False:
                return False

        return True

    def clear(self):
        for _writer in self._writer:
            _writer.clear()
        return

    def raw(self, content: str):
        _message = Message(content=content, raw=True)
        self.append(_message)
        return

    def inform(self, tag: str, content: str):
        _message = Message(tag=tag, content=content, level="INFORM")
        self.append(_message)
        return

    def warn(self, tag: str, content: str):
        _message = Message(tag=tag, content=content, level="WARN")
        self.append(_message)
        return

    def debug1(self, tag: str, content: str):
        _message = Message(tag=tag, content=content, level="DEBUG1")
        self.append(_message)
        return

    def debug2(self, tag: str, content: str):
        _message = Message(tag=tag, content=content, level="DEBUG2")
        self.append(_message)
        return

    def debug3(self, tag: str, content: str):
        _message = Message(tag=tag, content=content, level="DEBUG3")
        self.append(_message)
        return

    def error(self, content: str):
        _message = Message(content=content, level="ERROR")
        self.append(_message)
        return

    def exception(self, e: Exception):
        content = "An exception of type {0} occurred.".format(type(e).__name__)
        _message = Message(content=content, level="EXCEPTION")
        self.append(_message)

        content = "Arguments:\n{0!r}".format(e.args)
        _message = Message(content=content, level="EXCEPTION")
        self.append(_message)
        return

    def traceback(self):

        ttype, value, tb = sys.exc_info()
        self.error("Uncaught exception")
        self.error("Type:  " + str(ttype))
        self.error("Value: " + str(value))

        lines = traceback.format_tb(tb)
        for line in lines:
            _message = Message(content=line, raw=True)
            self.append(_message)
        return

    def progress(self, limit: int, interval: int = 0) -> Progress:
        _progress = Progress(limit, interval, self.append)
        return _progress

    def timer(self, content: str) -> Timer:
        _timer = Timer(content, self.append)
        return _timer
