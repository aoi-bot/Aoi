from discord.ext import commands


class RoleError(commands.CommandError):
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
