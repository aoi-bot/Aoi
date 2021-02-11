from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING, Tuple, Callable

from discord.ext import commands

if TYPE_CHECKING:
    from .aoi_bot import AoiBot


def friendly_signature(command: commands.Command, bot: AoiBot) -> str:
    callback: Callable = command.callback
    signature_string = []
    defaults = {}
    signature: inspect.Signature = inspect.signature(command.callback)
    param: inspect.Parameter
    for param in signature.parameters.values():
        if param.name in ("self", "ctx"):
            continue
        signature_string.append(
            f"""<a data-bs-toggle="tooltip" data-bs-placement="top" href="#" data-bs-html="true" 
            title="Default: <code>{param.default}</code>" >
            &lt;{param.name}&gt;</a>"""
            if param.default is not inspect.Parameter.empty else param.name)  # noqa
        if param.default is not inspect.Parameter.empty:
            defaults[param.name] = param.default
    result = " ".join(signature_string), defaults
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
    if command.aliases:
        if len(command.aliases) == 1:
            aliases = f"""<div>Alias: <code>,{command.aliases[0]}</code></div>"""
        else:
            aliases_joined = ", ".join(f"<code>,{alias}</code>" for alias in command.aliases)
            aliases = f"""<div>Aliases: {aliases_joined}</div>"""
    if command.flags:
        flags = "<div>Flags:<ul>"
        for name, flag in command.flags.items():
            if not flag[0]:
                flags += f"<li><code>--{name}</code> {flag[1]}"
            else:
                flags += f"<li><code>--{name} [{flag[0].__name__.lower()}]</code> {flag[1]}"
        flags += "</ul></div>"
    p = bot.permissions_needed_for(command.name)
    permissions = ("<div>User Permissions Needed: " +
                   (" ".join([permissions_badge(x) for x in p]) if p else "") + "</div>") \
        if p else ""

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
       </div>
   </div>
</div>
"""


module_active = False


def get_tab_pair(cog: commands.Cog) -> Tuple[str, str]:
    global module_active
    show = "show" if not module_active else ""
    active = "active" if not module_active else ""
    module_active = True
    return (f"""
                <button class="nav-link my-1 {active} text-white" id="v-pills-{cog.qualified_name}-tab" 
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
            """
            )


# flake8: noqa
async def generate(bot: AoiBot):
    cog: commands.Cog
    command: commands.Command
    tab_list = ""
    json_list = {}
    panes = ""

    for cog in (bot.get_cog(name) for name in sorted(bot.cogs)):
        if cog.qualified_name in bot.cog_groups["Hidden"]:
            continue
        tab, pane = get_tab_pair(cog)
        tab_list += tab
        cog_html = ""
        for command in cog.get_commands():
            cog_html += await gen_card(command, bot)
        panes += pane.replace("#CONTENT#", cog_html)

    with open("website/commands.html", "w") as fp, open("gen_template.html", "r") as template:
        fp.write(template.read().replace("#TABS", tab_list).replace("#PANES", panes).replace("#BOT#", "Aoi"))

    with open("commands.json", "w") as fp:
        json.dump(json_list, fp, indent=2)
