from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from discord.ext import commands

if TYPE_CHECKING:
    from .aoi_bot import AoiBot

STYLE = """
"""


def get_tab_list(names: Iterable[str]):
    return '<ul class="tabs blue darken-3 black-text center-align tabs-fixed-width">' + \
           "".join(
               [f"""<li class="tab black-text"><a href="#{name.replace('/', "_")}" class="black-text">{name}</a></li>"""
                # noqa
                for name in names]) + \
           '</ul>'


# flake8: noqa
def generate(bot: AoiBot):
    cog: commands.Cog
    command: commands.Command

    groups = get_tab_list(filter(lambda x: x != "Hidden", bot.cog_groups))
    cog_html = ""
    list_tabs = {}

    for group, cogs in bot.cog_groups.items():
        if group == "Hidden":
            continue
        group2 = group.replace("/", "_")
        list_tabs[group] = f"""<div id="{group2}">""" + get_tab_list(cogs)
        for cog_name in sorted(cogs):
            cog = bot.get_cog(cog_name)
            cog_html = f"<div id={cog_name}>" \
                       f"<div class='card blue darken-4'>" \
                       f"<div class='card-content white-text'>" \
                       f"<span class='card-title'>{cog_name}</span>" \
                       f"<p>{cog.description}</p>" \
                       f"</div></div><hr/>\n"
            for command in cog.get_commands():
                if command.aliases:
                    aliases = "<br>Aliases: " + "&emsp;".join([f"<code>{alias}</code>" for alias in command.aliases])
                else:
                    aliases = ""
                signature, defaults = bot.get_signature_data(command)
                usage = f'Usage: <code>,{command.name} {signature}</code>'
                if defaults:
                    default = "<br>Defaults: <ul class='browser-default' style='margin-top:-2px'>" + \
                              "".join(f"<li style='margin-top:-1px'><code>{name}</code> = {value}</li>"
                                      for name, value in defaults.items()) + "</ul>"
                else:
                    default = ""
                cog_html += f"<div class='card blue darken-3'>" \
                            f"<div class='card-content white-text'>" \
                            f"<span class='card-title'>{command.name}</span>" \
                            f"<p>{command.brief}{aliases}<br>{usage}{default}</p>" \
                            f"</div></div>"
            cog_html += "</ul></div>"
            list_tabs[group] += cog_html
        list_tabs[group] += "</div>"

    with open("commands.html", "w") as fp:
        fp.write(f"""
        <html>
            <head>
                <title>Aoi Commands</title>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
                <style>{STYLE}</style>
            </head>
            <body onload="M.AutoInit();" class="black-text blue lighten-4">
                <nav class="blue darken-4">
                    <div class="nav-wrapper">
                        <img src="/assets/favicon.png" height="100%">
                        <a href="#" class="brand-logo left">Aoi</a>
                        <ul id="nav-mobile" class="hide-on-med-and-low right">
                            <li><a href="/">Home</a></li>
                            <li><a href="/commands">Commands</a></li>
                        </ul>
                    </div>
                </nav>
                </br>
                <div class="container">
                    <div class="row">
                        <div class="col s12">
                            {groups}
                        </div>
                        <div class="col">
                            {"".join(list_tabs.values())}
                        </div>
                    <div>
                </div>
            </body>
        </html>
        """)
