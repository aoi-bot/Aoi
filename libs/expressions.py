import logging
import math
import re
from dataclasses import dataclass
from typing import List, Union

import aoi
from discord.ext import commands

logging.getLogger("aoi").info("expr:Initializing the expression evaluator")


@dataclass
class _Operator:
    precedence: int
    func: callable
    arguments: int


def get_prime_factors(number):
    pfact = {}
    if number < 0:
        pfact[-1] = 1
    number = abs(number)
    if number == 1:
        pfact[1] = 1
        return pfact
    while number % 2 == 0:
        number = number // 2
        pfact[2] = pfact.get(2, 0) + 1
    for i in range(3, int(math.sqrt(number)) + 1, 2):
        while number % i == 0:
            number = number // i
            pfact[i] = pfact.get(i, 0) + 1
    if number > 2:
        pfact[number] = pfact.get(number, 0) + 1
    return pfact


def _inlimits(number):
    if number > 100000000000:
        raise commands.BadArgument("Number must be less than 100000000000")


_PRECEDENCE_DICT = {
    "^": _Operator(
        precedence=15,
        func=lambda x, y: x ** y,
        arguments=2
    ),
    "SQRT": _Operator(
        precedence=15,
        func=lambda x: x ** (1 / 2),
        arguments=1
    ),
    "*": _Operator(
        precedence=14,
        func=lambda x, y: x * y,
        arguments=2
    ),
    "//": _Operator(
        precedence=14,
        func=lambda x, y: x // y,
        arguments=2
    ),
    "/": _Operator(
        precedence=14,
        func=lambda x, y: x / y,
        arguments=2
    ),
    "%": _Operator(
        precedence=14,
        func=lambda x, y: x % y,
        arguments=2
    ),
    "NEG": _Operator(
        precedence=14,
        func=lambda x: -x,
        arguments=1
    ),
    "+": _Operator(
        precedence=13,
        func=lambda x, y: x + y,
        arguments=2
    ),
    "-": _Operator(
        precedence=13,
        func=lambda x, y: x - y,
        arguments=2
    ),
    "LOG": _Operator(
        precedence=12,
        func=lambda x: math.log(x, 10),
        arguments=1
    ),
    "LN": _Operator(
        precedence=12,
        func=lambda x: math.log(x),
        arguments=1
    ),
    "SIN": _Operator(
        precedence=12,
        func=lambda x: math.sin(x),
        arguments=1
    ),
    "COS": _Operator(
        precedence=12,
        func=lambda x: math.cos(x),
        arguments=1
    ),
    "TAN": _Operator(
        precedence=12,
        func=lambda x: math.tan(x),
        arguments=1
    ),
    "ASIN": _Operator(
        precedence=12,
        func=lambda x: math.asin(x),
        arguments=1
    ),
    "ACOS": _Operator(
        precedence=12,
        func=lambda x: math.acos(x),
        arguments=1
    ),
    "ATAN": _Operator(
        precedence=12,
        func=lambda x: math.atan(x),
        arguments=1
    ),
    "SINH": _Operator(
        precedence=12,
        func=lambda x: math.sinh(x),
        arguments=1
    ),
    "COSH": _Operator(
        precedence=12,
        func=lambda x: math.cosh(x),
        arguments=1
    ),
    "TANH": _Operator(
        precedence=12,
        func=lambda x: math.tanh(x),
        arguments=1
    ),
    "ASINH": _Operator(
        precedence=12,
        func=lambda x: math.asinh(x),
        arguments=1
    ),
    "ACOSH": _Operator(
        precedence=12,
        func=lambda x: math.acosh(x),
        arguments=1
    ),
    "ATANH": _Operator(
        precedence=12,
        func=lambda x: math.atanh(x),
        arguments=1
    ),
    "ABS": _Operator(
        precedence=12,
        func=lambda x: abs(x),
        arguments=1
    ),
    "AND": _Operator(
        precedence=11,
        func=lambda x, y: int(x) & int(y),
        arguments=2
    ),
    "OR": _Operator(
        precedence=10,
        func=lambda x, y: int(x) | int(y),
        arguments=2
    ),
    "XOR": _Operator(
        precedence=9,
        func=lambda x, y: int(x) ^ int(y),
        arguments=2
    ),
    "LAND": _Operator(
        precedence=8,
        func=lambda x, y: 1 if x and y else 0,
        arguments=2
    ),
    "LOR": _Operator(
        precedence=8,
        func=lambda x, y: 1 if x or y else 0,
        arguments=2
    ),
    "LXOR": _Operator(
        precedence=8,
        func=lambda x, y: 1 if (x or y) and not (x and y) else 0,
        arguments=2
    ),
    ">=": _Operator(
        precedence=7,
        func=lambda x, y: 1 if x >= y else 0,
        arguments=2
    ),
    "<=": _Operator(
        precedence=7,
        func=lambda x, y: 1 if x <= y else 0,
        arguments=2
    ),
    ">": _Operator(
        precedence=7,
        func=lambda x, y: 1 if x > y else 0,
        arguments=2
    ),
    "<": _Operator(
        precedence=7,
        func=lambda x, y: 1 if x < y else 0,
        arguments=2
    )
}

_CONSTANTS = {
    "PI": math.pi,
    "E": math.e
}


def _split_next_token(expression: str):
    part = ""
    expression = expression.strip()
    if expression[0] in "()":
        return expression[0], expression[1:]
    # noinspection PyShadowingNames
    for operator in _PRECEDENCE_DICT.keys():
        if expression.startswith(operator.lower()):
            part = operator
            return part, expression[len(part):]
    for const in _CONSTANTS.keys():
        if expression.startswith(const.lower()):
            part = const
            return part, expression[len(part):]
    part = re.match("[0-9.]+", expression)[0]
    return part, expression[len(part):]


def _tokenize(expression: str):
    tokens = []
    expression = expression.lower()
    while expression:
        token, expression = _split_next_token(expression)
        if not token:
            return tokens
        tokens.append(token)
    # turn numbers into numbers
    for i in range(len(tokens)):
        try:
            tokens[i] = float(tokens[i])
        except ValueError:
            pass
    return tokens


def _infix_to_postfix(infix: List[Union[str, float]]):  # noqa: C901
    stack = []
    postfix = []
    for current in infix:
        if isinstance(current, float) or current in _CONSTANTS:
            postfix.append(current)
        else:
            if current == "(":
                stack.append(current)
            elif current == ")":
                while True:
                    if not stack:
                        break
                    if stack[-1] == "(":
                        stack.pop()
                        break
                    postfix.append(stack.pop())
            elif (not stack) \
                    or stack[-1] == "(" \
                    or _PRECEDENCE_DICT[current].precedence > _PRECEDENCE_DICT[stack[-1]].precedence:
                stack.append(current)
            else:
                while True:
                    if not stack:
                        break
                    if stack[-1] == "(":
                        stack.append(current)
                        break
                    if _PRECEDENCE_DICT[current].precedence < _PRECEDENCE_DICT[stack[-1]].precedence:
                        break
                    postfix.append(stack.pop())
                stack.append(current)
    while stack:
        postfix.append(stack.pop())
    return postfix


async def evaluate(expression: str):
    try:
        tokenized = _tokenize(expression)
        postfix = _infix_to_postfix(tokenized)
    except:  # noqa
        raise aoi.CalculationSyntaxError
    stack = []
    for token in postfix:
        try:
            if isinstance(token, float):
                stack.append(token)
            elif token in _CONSTANTS:
                stack.append(_CONSTANTS[token])
            else:
                operands = [stack.pop() for n in range(_PRECEDENCE_DICT[token].arguments)]
                stack.append(_PRECEDENCE_DICT[token].func(*reversed(operands)))
        except ValueError as err:
            if str(err) == "math domain error":
                raise aoi.DomainError(token)
            raise
        except:  # noqa
            raise aoi.MathError
    return stack[0]
