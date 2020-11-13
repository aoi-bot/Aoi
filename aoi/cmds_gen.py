from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from discord.ext import commands

if TYPE_CHECKING:
    from .aoi_bot import AoiBot

STYLE = """
div.fill {width: 100% !important;}
span.card-title {font-weight: bold;}
"""

TAB_BACKGROUND = "deep-purple darken-4"
TAB_TEXT = "white-text"
NAV_BACKGROUND = "deep-purple darken-4"
CARD_TEXT = "white-text"
CARD_BACKGROUND = "purple darken-2"
DESCRIPTION_TEXT = "white-text"
DESCRIPTION_BACKGROUND = "purple darken-4"
DEFAULT_TEXT = "white-text"
BODY_BACKGROUND = "blue lighten-3"

def get_tab_list(names: Iterable[str]):
    return f'<ul class="tabs {TAB_BACKGROUND} {TAB_TEXT} center-align fill">' + \
           "".join(
               [f"""<li class="tab {TAB_TEXT} fill"><a href="#{name.replace('/', "_").replace(" ", "_")
               }" class="{TAB_TEXT}">{name}</a></li>"""
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
        group2 = group.replace("/", "_").replace(" ", "_")
        list_tabs[group] = f"""<div id="{group2}" class='fill'>""" + get_tab_list(cogs)
        for cog_name in sorted(cogs):
            cog = bot.get_cog(cog_name)
            cog_html = f"<div id={cog_name} class='fill'>" \
                       f"<div class='card {DESCRIPTION_BACKGROUND}'>" \
                       f"<div class='card-content {DESCRIPTION_TEXT}'>" \
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
                p = bot.permissions_needed_for(command.name)
                permissions = ("<br>User Permissions Needed: " +
                               ", ".join(" ".join(map(lambda x: x.title(), x.split("_"))) for x in p)) \
                    if p else ""
                cog_html += f"<div class='card {CARD_BACKGROUND}'>" \
                            f"<div class='card-content {CARD_TEXT}'>" \
                            f"<span class='card-title'>{command.name}</span>" \
                            f"<p>{command.brief}{aliases}<br>{usage}{default}{permissions}</p>" \
                            f"</div></div>"
            cog_html += "</div>"
            list_tabs[group] += cog_html
        list_tabs[group] += "</div>"

    with open("commands.html", "w") as fp:
        fp.write(f"""

                </br>
                <div class="container">
                    <div class="row">
                        <div class="col s12">
                            {groups}
                        </div>
                        <div class="col s12">
                            {"".join(list_tabs.values())}
                        </div></div></div>
                    <div>
                </div>
        """)
