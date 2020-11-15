import inspect
from typing import Optional, Tuple

import aoi
import discord
from discord.ext import commands


async def _can_run(_c: commands.Command, ctx: aoi.AoiContext):
    for check in _c.checks:
        try:
            if inspect.iscoroutinefunction(check):
                x = await check(ctx)
            else:
                x = check(ctx)
            if not x:
                return False
        except discord.DiscordException:
            return False
    else:
        return True


class Help(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Help module"

    @commands.command(brief="Lists Aoi's modules", aliases=["mdls"])
    async def modules(self, ctx: aoi.AoiContext):
        s = ""
        for grp_name, cogs in self.bot.cog_groups.items():
            if grp_name == "Hidden":
                continue
            s += f"\n**{grp_name}**\n"
            for cog in cogs:
                c = self.bot.get_cog(cog)
                if c.description:
                    s += f"◆ **{c.qualified_name}** - {c.description}\n"
        await ctx.embed(title="Modules", description=s.strip(),
                        footer=f"Do {ctx.clean_prefix}commands module_name to view commands in a module",
                        thumbnail=self.bot.user.avatar_url)

    @commands.command(brief="Lists commands within a module", name="commands",
                      aliases=["cmds"],
                      flags={"all": (None, "Include the commands you can't use")})
    async def cmds(self, ctx: aoi.AoiContext, module: str):
        flags = ctx.flags
        cog: commands.Cog = self.bot.get_cog(self.bot.find_cog(module, check_description=True)[0])
        c: commands.Command
        yes = ":white_check_mark:"
        no = ":x:"
        if "all" in flags:
            built = "\n".join(
                [f"{yes if await _can_run(c, ctx) else no} **{c.name}** - {c.brief}" for c in cog.get_commands()]
            )
        else:
            built = "\n".join(
                [f"**{c.name}** - {c.brief}" for c in cog.get_commands() if await _can_run(c, ctx)]
            )
        await ctx.embed(
            title=f"Commands for {cog.qualified_name} module",
            description=cog.description + "\n\n" + built,
            footer=f"Do {ctx.clean_prefix}help command_name for help on a command, "
                   f"and {ctx.clean_prefix}cmds {module} --all to view all commands for the module"
        )

    @commands.command(brief="Shows help for a command", aliases=["h"])
    async def help(self, ctx: aoi.AoiContext, command: str = None):
        if not command:
            return await ctx.embed(title="Aoi Help",
                                   fields=[("Module List", f"`{ctx.clean_prefix}modules` to view "
                                                           f"the list of Aoi's modules"),
                                           ("Module Commands", f"`{ctx.clean_prefix}commands module_name` "
                                                               f"to view commands in a module"),
                                           ("Command Help", f"`{ctx.clean_prefix}help command_name` to "
                                                            f"view help for a command"),
                                           ("Other Guides", f"`{ctx.clean_prefix}cmds guides` to "
                                                            f"view the guides"),
                                           ("Support Server", f"Still need help? Join our [support "
                                                              f"server](https://discord.gg/pCgEj8t)"),
                                           ("Command List", f"View Aoi's [command list]"
                                                            f"(https://www.aoibot.xyz/commands.html)"),
                                           ("Voting", f"Vote for Aoi [here]"
                                                      f"(https://top.gg/bot/738856230994313228)")
                                           ],
                                   not_inline=[2, 3, 4])
        cmd: commands.Command = self.bot.get_command(command.lower())
        if not cmd:
            return await ctx.send_error(f"Command `{command}` not found.")
        p = self.bot.permissions_needed_for(cmd.name)
        flags = cmd.flags

        def format_flag(flag_tup: Tuple[str, Tuple[Optional[type], str]]):
            if flag_tup[1][0]:
                return f"◆`--{flag_tup[0]} <{flag_tup[1][0].__name__}>` - {flag_tup[1][1]}"
            else:
                return f"◆`--{flag_tup[0]}` - {flag_tup[1][1]}"

        await ctx.embed(
            title=cmd.name,
            fields=[
                       ("Usage", f"`{cmd.name} {cmd.signature or ''}" + (" [flags]`" if flags else "`")),
                       ("Description", cmd.brief),
                       ("Module", cmd.cog.qualified_name)
                   ] + (
                       [("User permissions needed",
                         ", ".join(
                             " ".join(map(lambda x: x.title(), x.split("_"))) for x in p
                         ))] if p else []
                       if not await _can_run(cmd, ctx) else []
                   ) + (
                       [("Missing Permissions", "You are missing the permissions to run this command")]
                       if not await _can_run(cmd, ctx) else []
                   ) + (
                       [("Flags", "\n".join(map(str, map(format_flag, flags.items()))))]
                       if flags else []
                   ) + (
                       [("Aliases", ", ".join([f"`{a}`" for a in cmd.aliases]))]
                       if cmd.aliases else []
                   ),
            footer="<> indicate required parameters, [] indicate optional parameters",
            not_inline=[0, 1, 2, 3]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Help(bot))
