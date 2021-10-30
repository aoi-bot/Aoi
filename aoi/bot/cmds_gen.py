from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING, Callable, Dict, Tuple, Union

from discord.ext import commands

from aoi.libs.linq import LINQ

if TYPE_CHECKING:
    from .aoi_bot import AoiBot


def type_string(annotation) -> str:
    if hasattr(annotation, "__name__"):
        if annotation.__name__ == "_empty":
            return "str"
        if not annotation.__name__.startswith("_"):
            return annotation.__name__
    s = str(annotation)
    if s.startswith("typing.Union"):
        args = s.replace("typing.Union[", "").replace("]", "").split(", ")
        if "NoneType" in args:
            args.remove("NoneType")
            return f"Optional {args[0]}"
        else:
            return "</code> or <code>".join(a.split(".")[-1] for a in args)
    if "_Greedy" in str(annotation):
        if "<class" in str(annotation.converter):
            return f"{type_string(annotation.converter)}(s)"
        if "Union" in str(annotation.converter):
            return f"{type_string(annotation.converter)}(s)"
        return "str"

    return "<b>Unknown Type</b>"


def friendly_signature(command: commands.Command, bot: AoiBot) -> str:
    callback: Callable = command.callback
    signature_string = []
    defaults = {}
    signature: inspect.Signature = inspect.signature(command.callback)
    param: inspect.Parameter
    for param in signature.parameters.values():
        if param.name in ("self", "ctx"):
            continue
        if param.default is not inspect.Parameter.empty:
            signature_string.append(
                f"""<span data-bs-toggle="tooltip" data-bs-placement="top" href="#" data-bs-html="true" 
                title="Type: <code>{type_string(param.annotation)}</code><br/>Default: <code>{param.default}</code><br/>Optional" 
                class="argument default">
                &lt;{param.name}&gt;</span>"""
            )  # noqa
        else:
            signature_string.append(
                f"""<span data-bs-toggle="tooltip" data-bs-placement="top" href="#" data-bs-html="true" 
                title="Type: <code>{type_string(param.annotation)}</code>" 
                class="argument required">
                {param.name}</span>"""
            )  # noqa
        if param.default is not inspect.Parameter.empty:
            defaults[param.name] = param.default
    " ".join(signature_string), defaults
    return " ".join(signature_string)


def permissions_badge(permission: str) -> str:
    permission = " ".join(map(lambda x: x.title(), permission.split("_")))
    if permission == "Owner Only":
        return """
        <span class="badge bg-danger my-1 mx-1" data-bs-toggle="tooltip" title="You must be selfhosting this bot to 
        use this command" data-bs-placement="top">Owner Only</span>
        """
    if "Manage" in permission:
        typ = "success"
    else:
        typ = "primary"
    return f"""<span class="badge bg-{typ} my-1 mx-1">{permission}</span>"""


async def gen_card(command: commands.Command, bot: AoiBot) -> str:
    aliases = ""
    flags = ""
    examples = ""
    if command.aliases:
        if len(command.aliases) == 1:
            aliases = f"""<div>Alias: <code>,{command.aliases[0]}</code></div>"""
        else:
            aliases_joined = ", ".join(
                f"<code>,{alias}</code>" for alias in command.aliases
            )
            aliases = f"""<div>Aliases: {aliases_joined}</div>"""
    if command.flags:
        flags = "<div>Flags:<ul>"
        for name, flag in command.flags.items():
            if not flag[0]:
                flags += f"<li><code>--{name}</code> {flag[1]}"
            else:
                flags += (
                    f"<li><code>--{name} [{flag[0].__name__.lower()}]</code> {flag[1]}"
                )
        flags += "</ul></div>"
    if command.description:
        examples = (
            "<div>Examples:<ul>"
            + LINQ(command.description.splitlines())
            .select(lambda x: f"<li><code>,{x}</code>")
            .join("\n")
            + "</ul></div>"
        )
    p = bot.permissions_needed_for(command.name)
    permissions = (
        (
            "<div>User Permissions Needed: "
            + (" ".join([permissions_badge(x) for x in p]) if p else "")
            + "</div>"
        )
        if p
        else ""
    )

    return f"""
<div class="card bg-dark my-1 mx-1">
    <div class="card-body">
        <h5 class="card-title"><code>,{command.name}</code></h5>
        <h6 class="card-subtitle text-muted">{command.brief}</h6>
        <div class="card-text">
           {aliases}
           <div>
              Usage: <code>,{command.name} {friendly_signature(command, bot)}</code>
           </div>
           {flags}
           {permissions}
           {examples}
       </div>
   </div>
</div>
""".replace(
        "#BOT#", "Aoi"
    ).replace(
        "{prefix}", ","
    )


module_active = False


def get_tab_pair(cog: commands.Cog) -> Tuple[str, str, str]:
    global module_active
    show = "show" if not module_active else ""
    active = "active" if not module_active else ""
    module_active = True
    return (
        f"""
                <button class="nav-link my-1 {active} text-white"
                        data-bs-toggle="pill" data-bs-target="#v-pills-{cog.qualified_name}"
                        type="button" role="tab" aria-controls="v-pills-{cog.qualified_name}" aria-selected="true">
                        {cog.qualified_name}
                </button>
""",
        f"""
                <div class="tab-pane fade my-3 mx-4 {show} {active} text-white" id="v-pills-{cog.qualified_name}" 
                    role="tabpanel" aria-labelledby="v-pills-{cog.qualified_name}-tab">
                    <h2 class="mx-2 my-2">{cog.qualified_name}</h2>
                    <h4 class="mx-2 my-2">{cog.description}</h4>
                    #CONTENT#
                </div>
            """,
        f"""
                <button class="nav-link my-1 {active} text-white mobile-nav"
                        data-bs-toggle="pill" data-bs-target="#v-pills-{cog.qualified_name}"
                        type="button" role="tab" aria-controls="v-pills-{cog.qualified_name}" aria-selected="true">
                        {cog.qualified_name}
                </button>
""",
    )


# flake8: noqa
async def generate(bot: AoiBot):
    cog: commands.Cog
    command: commands.Command
    tab_list = ""
    tab_list_2 = ""
    commands_json: Dict[str, Dict[str, Union[str, Dict[str, str]]]] = {}
    panes = ""

    for cog in (bot.get_cog(name) for name in sorted(bot.cogs)):
        if cog.qualified_name in bot.cog_groups["Hidden"]:
            continue
        commands_json[cog.qualified_name] = {
            "description": cog.description,
            "commands": {},
        }
        tab, pane, tab2 = get_tab_pair(cog)
        tab_list += tab
        tab_list_2 += tab2
        cog_html = ""
        for command in cog.get_commands():
            card = await gen_card(command, bot)
            cog_html += card
            commands_json[cog.qualified_name]["commands"][command.name] = card
        panes += pane.replace("#CONTENT#", cog_html)

    with open("complexity/context/commands.json", "w") as fp:
        json.dump(commands_json, fp, indent=4)
