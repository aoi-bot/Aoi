"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import typing

import tanjun

_descriptions: dict[tanjun.abc.MessageCommand, str] = {}
_hidden: list[tanjun.abc.MessageCommand] = []


class HelpClient:
    def __init__(self):
        pass

    @staticmethod
    def get_help_for(command_name: typing.Union[str, tanjun.abc.MessageCommand]) -> typing.Optional[str]:
        if isinstance(command_name, tanjun.abc.MessageCommand):
            command_name = typing.cast(list[str], command_name.names)[0]
        for command, help_str in _descriptions.items():
            if command_name in command.names:
                return help_str

    @staticmethod
    def is_hidden(command_name: typing.Union[str, tanjun.abc.MessageCommand]) -> bool:
        if isinstance(command_name, tanjun.abc.MessageCommand):
            command_name = typing.cast(list[str], command_name.names)[0]
        for command in _hidden:
            if command_name in command.names:
                return True
        return False

    @staticmethod
    def is_visible(command_name: typing.Union[str, tanjun.abc.MessageCommand]) -> bool:
        if isinstance(command_name, tanjun.abc.MessageCommand):
            command_name = typing.cast(list[str], command_name.names)[0]
        for command in _hidden:
            if command_name in command.names:
                return False
        return True


def with_description(
    description: str,
) -> typing.Callable[[tanjun.abc.MessageCommand], tanjun.abc.MessageCommand]:
    def deco(command: tanjun.abc.MessageCommand):
        _descriptions[command] = description
        return command

    return deco


def as_hidden(command: tanjun.abc.MessageCommand) -> tanjun.abc.MessageCommand:
    if command in _hidden:
        raise ValueError("Command already hidden")
    _hidden.append(command)
    return command
