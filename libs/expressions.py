import logging
import re
from dataclasses import dataclass
from typing import List, Union
import math
import aoi
logging.info("expr:Initializing the expression evaluator")


@dataclass
class _Operator:
    precedence: int
    func: callable
    arguments: int


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
        func=lambda x, y: x & y,
        arguments=2
    ),
    "OR": _Operator(
        precedence=10,
        func=lambda x, y: x | y,
        arguments=2
    ),
    "XOR": _Operator(
        precedence=9,
        func=lambda x, y: x ^ y,
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


def _infix_to_postfix(infix: List[Union[str, float]]):
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
    except:
        raise aoi.SyntaxError
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
        except:
            raise aoi.MathError
    return stack[0]
