from typing import List

from discord.ext import commands


class RoleHierarchyError(commands.CommandError):
    pass


class PermissionFailed(commands.CommandError):
    pass


class MathError(BaseException):
    pass


class DomainError(MathError):
    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop("token")
        super(DomainError, self).__init__(*args, *kwargs)


class CalculationSyntaxError(MathError):
    pass


class CurrencyError(commands.CommandError):
    def __init__(self, *args, **kwargs):
        self.amount_has: int = kwargs.pop("amount_has")
        self.amount_needed: int = kwargs.pop("amount_needed")
        self.is_global: bool = kwargs.pop("is_global")
        super(CurrencyError, self).__init__(*args, **kwargs)
