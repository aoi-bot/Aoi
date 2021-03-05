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

    @commands.command(brief="Lists #BOT#'s modules", aliases=["mdls"])
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
        if not await ctx.using_embeds():
            return await ctx.send(f"**__Modules__**\n"
                                  f"{s.strip()}\n"
                                  f"Do {ctx.clean_prefix}commands module_name` to view commands in a module")
        await ctx.embed(title="Modules", description=s.strip(),
                        footer=f"Do {ctx.clean_prefix}commands module_name to view commands in a module",
                        thumbnail=self.bot.random_thumbnail())

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
                [
                    f"{yes if await _can_run(c, ctx) else no} **{c.name}** - "
                    f"{c.brief.replace('#BOT#', self.bot.user.name)}"
                    for c in cog.get_commands()
                ]
            )
        else:
            built = "\n".join(
                [
                    f"**{c.name}** - {c.brief.replace('#BOT#', self.bot.user.name)}"
                    for c in cog.get_commands() if await _can_run(c, ctx)
                ]
            )
        if not await ctx.using_embeds():
            return await ctx.send(f"**__Commands for {cog.qualified_name} module__**\n"
                                  f"> {cog.description}\n\n"
                                  f"{built}\n\n"
                                  f"Do `{ctx.clean_prefix}help command_name` for help on a command, "
                                  f"and `{ctx.clean_prefix}cmds {module} --all` to view all commands for the module"
                                  )
        await ctx.embed(
            title=f"Commands for {cog.qualified_name} module",
            description=cog.description + "\n\n" + built,
            footer=f"Do {ctx.clean_prefix}help command_name for help on a command, "
                   f"and {ctx.clean_prefix}cmds {module} --all to view all commands for the module",
            thumbnail=self.bot.random_thumbnail()
        )

    @commands.command(brief="Shows help for a command", aliases=["h"])
    async def help(self, ctx: aoi.AoiContext, command: str = None):
        if not command:
            return await ctx.embed(title="Help",
                                   fields=  # noqa E251
                                   [("Module List", f"`{ctx.clean_prefix}modules` to view "
                                                    f"the list of {self.bot.user.name if self.bot.user else ''}'s "
                                                    f"modules"),
                                    ("Module Commands", f"`{ctx.clean_prefix}commands module_name` "
                                                        f"to view commands in a module"),
                                    ("Command Help", f"`{ctx.clean_prefix}help command_name` to "
                                                     f"view help for a command"),
                                    ("Other Guides", f"`{ctx.clean_prefix}cmds help` to "
                                                     f"view the guides or check out the [online guides]"
                                                     f"(https://www.aoibot.xyz/guides.html)"),
                                    ("Support Server", f"Still need help? Join our [support "
                                                       f"server](https://discord.gg/zRvNtXFWeS)"),
                                    ("Command List",
                                     f"View {self.bot.user.name if self.bot.user else ''}'s [command list]"
                                     f"(https://www.aoibot.xyz/commands.html)"),
                                    ] + (
                                       [
                                           ("Voting", f"Vote for Aoi [here]"
                                                      f"(https://top.gg/bot/791265892154867724)")
                                       ] if self.bot.user.id == 791265892154867724 else []
                                   ),
                                   thumbnail=self.bot.random_thumbnail(),
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

        if not await ctx.using_embeds():
            return await ctx.send(
                f"__`{cmd.name}`__\n"
                f"Usage: `{ctx.prefix}{cmd.name} {cmd.signature or ''}{' [flags]' if flags else ''}`\n"
                f"Description: {cmd.brief.replace('#BOT#', self.bot.user.name if self.bot.user else '')}\n"
                f"Module: {cmd.cog.qualified_name}\n" +
                (("User permissions needed: " +
                  ", ".join(
                      " ".join(map(lambda x: x.title(), x.split("_"))) for x in p
                  ) + "\n") if p else '') +
                ("You are missing permissions needed to turn this command\n" if not await _can_run(cmd, ctx) else '') +
                (("Flags:\n" + "\n".join(map(str, map(format_flag, flags.items()))) + "\n") if flags else "") +
                (("Aliases:" + ", ".join([f"`{a}`" for a in cmd.aliases])) if cmd.aliases else "") +
                (f"\nAliases are pointing at this command, run `{ctx.clean_prefix}aliases {command}` to view them\n"
                 if self.bot.rev_alias(ctx, command) else "") +
                "\n<> indicate required parameters, [] indicate optional parameters"
            )

        await ctx.embed(
            title=cmd.name,
            fields=[
                       ("Usage", f"`{cmd.name} {cmd.signature or ''}" + (" [flags]`" if flags else "`")),
                       ("Description", cmd.brief.replace("#BOT#", self.bot.user.name if self.bot.user else '')),
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
                   ) + (
                       [("Active aliases", ", ".join([f"`{a}`" for a in cmd.aliases]))]
                       if self.bot.rev_alias(ctx, command) else []
                   ),
            thumbnail=self.bot.random_thumbnail(),
            footer="<> indicate required parameters, [] indicate optional parameters",
            not_inline=[0, 1, 2, 3, 4]
        )

    @commands.command(brief="Shows the permission guide")
    async def permguide(self, ctx: aoi.AoiContext):
        await ctx.send_info(f"\n"
                            f"{self.bot.user.name if self.bot.user else ''}'s permissions are based off of a permission chain that "
                            f"anyone can view with `{ctx.prefix}lp`. The chain is evaluated "
                            f"from 0 to the top. The permission chain can be modified by anyone with "
                            f"administrator permission in a server. `{ctx.prefix}cmds permissions` can "
                            f"be used to view view a list of the permission commands\n"
                            f"The chain can be reset to the default with {ctx.prefix}rp"
                            )

    @commands.command(
        brief="Shows the currency guide"
    )
    async def currencyguide(self, ctx: aoi.AoiContext):
        await ctx.send_info(f"\n"
                            f"There are two types of currency in {self.bot.user.name if self.bot.user else ''}: "
                            f"Server and Global.\nGlobal currency is gained at the rate of $3/message, and can only "
                            f"be gained once every 3 minutes. Global currency is used over in "
                            f"`{ctx.prefix}cmds globalshop` to "
                            f"buy a title for your card an over in `{ctx.prefix}profilecard` to buy a background change "
                            f"for your profile card.\n"
                            f"Server currency is gained at a rate set by the server staff, and is viewable with "
                            f"`{ctx.prefix}configs`. It is used for roles and gambling - see `{ctx.prefix}cmds ServerShop` "
                            f"and `{ctx.prefix}cmds ServerGambling`."
                            )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Help(bot))
