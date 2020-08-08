from discord.ext import commands


class RoleError(commands.CommandError):
    pass


class PermissionFailed(commands.CommandError):
    pass
