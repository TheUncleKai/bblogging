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

from enum import Enum


__all__ = [
    "Type",
    "Data",
    "Convert"
]


class Type(Enum):
    """Entry types."""

    Float = float
    """represent an integer."""

    Number = int
    """represent an integer."""

    String = str
    """represent a string."""

    Boolean = bool
    """represent a boolean."""

    Array = list
    """represent an array."""

    Tuple = tuple
    """represent an tuple."""

    Object = dict
    """represent a dictionary type object."""

    Null = None
    """represent none."""


class Data(object):

    def __init__(self, **kwargs):

        self._id = kwargs.get("id", "")
        keys = kwargs.get("keys", None)
        values = kwargs.get("values", None)

        if (keys is None) or (values is None):
            return

        for (key, value) in zip(keys, values):
            self.__dict__[key] = value
        return

    def __str__(self) -> str:
        return self._id


class Convert(object):

    def __init__(self):
        return

    @staticmethod
    def check_name(name: str) -> bool:
        white_list = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

        for char in name:
            if char in white_list:
                continue
            else:
                raise ValueError("Invald character {0:s} in name: {1:s}".format(char, name))

        return True

    def _convert_list(self, data: list) -> list:
        """Convert dict or die.

        :param data: data item.
        :type data: list

        :return: list object or None.
        """

        values = []

        for item in data:
            value, check = self._convert("", item)
            if check is True:
                values.append(value)

        return values

    def _convert_dict(self, name: str, data: dict):
        """Convert dict or die.

        :param name: item name.
        :type name: str

        :param data: data item.
        :type data: dict

        :return: data object or None.
        """

        names = []
        values = []

        for key in list(data):
            item = data[key]
            check = self.check_name(key)
            if check is False:
                return None
            value, check = self._convert(key, item)
            if check is False:
                return None

            names.append(key)
            values.append(value)

        if (len(names) == 0) or (len(values) == 0):  # pragma: no cover
            return None

        config = Data(id=name, keys=names, values=values)
        return config

    def _convert(self, itemid: str, data):
        """Convert item or die.

        :param itemid: root id.
        :type itemid: str

        :param data: item data.

        :return: data object or None and if conversion was successfull
        :rtype: tuple
        """

        type_data = type(data)

        check_object = type_data is Type.Object.value
        check_array = type_data is Type.Array.value
        check_tuple = type_data is Type.Tuple.value

        check_string = type_data is Type.String.value
        check_number = type_data is Type.Number.value
        check_float = type_data is Type.Float.value
        check_boolean = type_data is Type.Boolean.value
        check_null = data is Type.Null.value

        value = None
        valid = False

        if check_object is True:
            value = self._convert_dict(itemid, data)
            valid = True

        if check_array is True:
            value = self._convert_list(data)
            valid = True

        if check_tuple is True:
            value = self._convert_list(data)
            valid = True

        if check_string is True:
            value = data
            valid = True

        if check_number is True:
            value = data
            valid = True

        if check_float is True:
            value = data
            valid = True

        if check_boolean is True:
            value = data
            valid = True

        if check_null is True:
            valid = True

        if (value is None) and (check_object is False) and (check_null is False):
            raise ValueError("Invalid data type for {0:s}".format(itemid))

        return value, valid

    def parse(self, data):
        """Parse given data.

        :return: converted data or none.
        """
        ret, _ = self._convert("", data)
        return ret
