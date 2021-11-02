import inspect
from typing import List

import discord
from discord.ext import commands

from aoi import bot
from dpy_stuff.cog_helpers.help import HelpCogService
from aoi.libs.linq import LINQ


async def _can_run(_c: commands.Command, ctx: bot.AoiContext):
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


class Help(commands.Cog, HelpCogService):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Help module"

    @commands.command(brief="Lists #BOT#'s modules", aliases=["mdls"])
    async def modules(self, ctx: bot.AoiContext):
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
            return await ctx.send(
                f"**__Modules__**\n"
                f"{s.strip()}\n"
                f"Do {ctx.clean_prefix}commands module_name` to view commands in a module"
            )
        await ctx.embed(
            title="Modules",
            description=s.strip(),
            footer=f"Do {ctx.clean_prefix}commands module_name to view commands in a module",
            thumbnail=self.bot.random_thumbnail(),
        )

    @commands.command(
        brief="Lists commands within a module",
        name="commands",
        aliases=["cmds"],
        flags={"all": (None, "Include the commands you can't use")},
        description="""
                      cmds
                      cmds Roles
                      cmds Roles --all
                      """,
    )
    async def cmds(self, ctx: bot.AoiContext, module: str):
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
                    for c in cog.get_commands()
                    if await _can_run(c, ctx)
                ]
            )
        if not await ctx.using_embeds():
            return await ctx.send(
                f"**__Commands for {cog.qualified_name} module__**\n"
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
            thumbnail=self.bot.random_thumbnail(),
        )

    @commands.command(
        brief="Shows help for a command",
        aliases=["h"],
        description="""
                      help
                      help command_name
                      """,
    )
    async def help(self, ctx: bot.AoiContext, command: str = None):
        if not command:
            return await ctx.embed(
                title="Help",
                fields=[  # noqa E251
                    (
                        "Module List",
                        f"`{ctx.clean_prefix}modules` to view "
                        f"the list of {self.bot.user.name if self.bot.user else ''}'s "
                        f"modules",
                    ),
                    (
                        "Module Commands",
                        f"`{ctx.clean_prefix}commands module_name` " f"to view commands in a module",
                    ),
                    (
                        "Command Help",
                        f"`{ctx.clean_prefix}help command_name` to " f"view help for a command",
                    ),
                    (
                        "Other Guides",
                        f"`{ctx.clean_prefix}cmds help` to "
                        f"view the guides or check out the [online guides]"
                        f"(https://www.aoibot.xyz/guides.html)",
                    ),
                    (
                        "Support Server",
                        f"Still need help? Join our [support " f"server](https://discord.gg/6VusqNUr9V)",
                    ),
                    (
                        "Command List",
                        f"View {self.bot.user.name if self.bot.user else ''}'s [command list]"
                        f"(https://www.aoibot.xyz/commands.html)",
                    ),
                ]
                + (
                    [
                        (
                            "Voting",
                            f"Vote for Aoi [here]" f"(https://top.gg/bot/791265892154867724)",
                        )
                    ]
                    if self.bot.user.id == 791265892154867724
                    else []
                ),
                thumbnail=self.bot.random_thumbnail(),
                not_inline=[2, 3, 4],
            )
        cmd: commands.Command = self.bot.get_command(command.lower())
        if not cmd:
            return await ctx.send_error(f"Command `{command}` not found.")
        p = self.bot.permissions_needed_for(cmd.name)
        flags = cmd.flags

        if not await ctx.using_embeds():
            return await ctx.send(
                f"__`{cmd.name}`__\n"
                f"Usage: `{self.get_command_signature(cmd, ctx)}`\n"
                # *prays the pep8 gods won't strike me down for this 145 character line*
                # Just let me have my f-strings D:
                f"Description: {cmd.brief.replace('#BOT#', self.bot.user.name if self.bot.user else '').replace('{prefix}', ctx.clean_prefix)}\n"  # noqa E501
                f"Module: {cmd.cog.qualified_name}\n"
                + (("Flags:\n" + "\n".join(map(str, map(self.format_flag, flags.items()))) + "\n") if flags else "")
                + (
                    (
                        "User permissions needed: "
                        + ", ".join(" ".join(map(lambda x: x.title(), x.split("_"))) for x in p)
                        + "\n"
                    )
                    if p
                    else ""
                )
                + ("You are missing permissions needed to turn this command\n" if not await _can_run(cmd, ctx) else "")
                + (
                    "Examples:\n"
                    + LINQ(cmd.description.splitlines())
                    .select(lambda x: x.strip())
                    .select(lambda x: f"⋄ `{ctx.clean_prefix}{x}`")
                    .join("\n")
                    + "\n"
                    if cmd.description
                    else ""
                )
                + (("Aliases:" + ", ".join([f"`{a}`" for a in cmd.aliases])) if cmd.aliases else "")
                + (
                    f"\nAliases are pointing at this command, run `{ctx.clean_prefix}aliases {command}` to view them\n"
                    if await self.bot.rev_alias(ctx, command)
                    else ""
                )
                + "\n[] indicates an optional parameter"
            )

        await ctx.embed(
            title=cmd.name,
            fields=[
                ("Usage", f"`{self.get_command_signature(cmd, ctx)}`"),
                (
                    "Description",
                    cmd.brief.replace("#BOT#", self.bot.user.name if self.bot.user else "").replace(
                        "{prefix}", ctx.clean_prefix
                    ),
                ),
                ("Module", cmd.cog.qualified_name),
            ]
            + ([("Flags", "\n".join(map(str, map(self.format_flag, flags.items()))))] if flags else [])
            + (
                [
                    (
                        "User permissions needed",
                        ", ".join(" ".join(map(lambda x: x.title(), x.split("_"))) for x in p),
                    )
                ]
                if p
                else []
                if not await _can_run(cmd, ctx)
                else []
            )
            + (
                [
                    (
                        "Missing Permissions",
                        "You are missing the permissions to run this command",
                    )
                ]
                if not await _can_run(cmd, ctx)
                else []
            )
            + (
                [
                    (
                        "Examples",
                        LINQ(cmd.description.splitlines())
                        .select(lambda x: x.strip())
                        .select(lambda x: f"⋄ `{ctx.clean_prefix}{x}`")
                        .join("\n"),
                    )
                ]
                if cmd.description
                else []
            )
            + ([("Aliases", ", ".join([f"`{a}`" for a in cmd.aliases]))] if cmd.aliases else []),
            thumbnail=self.bot.random_thumbnail(),
            footer="[] indicates an optional parameter",
            not_inline=[0, 1, 2, 3, 4],
        )

    @commands.command(brief="Searches through the help commands")
    async def helpsearch(self, ctx: bot.AoiContext, *, text_to_find: str):
        cmds: List[commands.Command] = []
        tokenized = text_to_find.lower().split(" ")
        cmd: commands.Command
        for cmd in self.bot.walk_commands():
            searchable_string = f"{cmd.name} {' '.join(cmd.aliases)} {cmd.usage} {cmd.description} {cmd.brief}".lower()
            if all(token in searchable_string for token in tokenized):
                cmds.append(cmd)
        await ctx.paginate(
            [
                f"**{cmd.name}** from **{cmd.cog.qualified_name}**: "
                f"{cmd.brief[:100] if cmd.brief else (cmd.description[:100] if cmd.description else '')}"
                for cmd in cmds
            ],
            n=20,
            title="Help search",
        )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(Help(bot))
