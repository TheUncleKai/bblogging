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

import abc
from abc import ABCMeta

from datetime import datetime

__all__ = [
    "Message",
    "Timer",
    "Progress",
    "Writer"
]


class Message(object):

    def __init__(self, **kwargs):
        self.time = datetime.now()
        self.app = ""
        self.tag = ""
        self.content = ""
        self.level = ""
        self.raw = False

        # noinspection PyTypeChecker
        self.progress = None

        item = kwargs.get("app", None)
        if item is not None:
            self.app = item

        item = kwargs.get("tag", None)
        if item is not None:
            self.tag = item

        item = kwargs.get("level", None)
        if item is not None:
            self.level = item

        item = kwargs.get("content", None)
        if item is not None:
            self.content = item

        item = kwargs.get("raw", None)
        if item is not None:
            self.raw = item

        item = kwargs.get("progress", None)
        if item is not None:
            self.progress = item
        return


class Timer(object):

    def __init__(self, content: str, append_callback):
        self.content = content
        self.start = datetime.now()
        self._append = append_callback
        return

    def stop(self):
        delta = datetime.now() - self.start
        content = "Runtime: {0:s} for {1:s}".format(str(delta), self.content)

        _message = Message(content=content, level="TIMER")
        self._append(_message)
        return


class Progress(object):

    def __init__(self, limit: int, interval: int, append_callback):
        self.limit = limit
        self.counter = 0
        self.value = 0.0
        self.finished = False
        self.interval = interval
        self.interval_counter = 0
        self.append = append_callback
        self.length = len(str(self.limit))
        return

    def _recalc(self):
        """recalculate progress.
        """
        self.value = float(self.counter) * 100.0 / float(self.limit)

        if self.interval != 0:
            self.interval_counter += 1
            if self.interval_counter == self.interval:
                self.interval_counter = 0

        if self.counter == self.limit:
            self.finished = True
        return

    def set(self, value: int):
        self.counter = value
        self._recalc()

        if self.interval_counter != 0:
            return

        _message = Message(level="PROGRESS", progress=self)
        self.append(_message)
        return

    def inc(self):
        self.counter += 1

        self._recalc()

        if self.interval_counter != 0:
            return

        _message = Message(level="PROGRESS", progress=self)
        self.append(_message)
        return

    def dec(self):
        self.counter -= 1

        self._recalc()

        if self.interval_counter != 0:
            return

        _message = Message(level="PROGRESS", progress=self)
        self.append(_message)
        return


class Writer(metaclass=ABCMeta):

    def __init__(self, name: str, index):
        self.id = name
        self.index = index
        return

    @abc.abstractmethod
    def setup(self, **kwargs):  # pragma: no cover
        return

    @abc.abstractmethod
    def write(self, item: Message):  # pragma: no cover
        return

    @abc.abstractmethod
    def clear(self) -> bool:  # pragma: no cover
        return True

    @abc.abstractmethod
    def open(self) -> bool:  # pragma: no cover
        return True

    @abc.abstractmethod
    def close(self) -> bool:  # pragma: no cover
        return True
