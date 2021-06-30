from bot import aoi
import discord
from discord.ext import commands


# TODO help refactor
class Quotes(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return "Store and retrieve quotes"

    @commands.command(brief="Adds a quote", aliases=["aq", "adq"])
    async def addquote(self, ctx: aoi.AoiContext, trigger: str, *, response: str):
        rowid = \
            (await self.bot.db.conn.execute_insert("insert into quotes (user, guild, name, content) values (?,?,?,?)",
                                                   (ctx.author.id, ctx.guild.id, trigger, response)))[0]
        await self.bot.db.conn.commit()
        await ctx.send_ok(f"Added quote **#{rowid}** - **{discord.utils.escape_markdown(trigger)}** - "
                          f"**{discord.utils.escape_markdown(str(ctx.author))}**")

    @commands.command(brief="Recalls a quote", aliases=["q"])
    async def quote(self, ctx: aoi.AoiContext, trigger: str):
        qid, content, user = (
            await (
                await self.bot.db.conn.execute("select id, content, user from quotes where guild=? and name=? "  # noqa
                                               "order by RANDOM() limit 1",
                                               (ctx.guild.id, trigger))
            ).fetchone())
        msg = await ctx.send_json(content)
        await msg.edit(
            content=f"Quote **{qid}** by "
                    f"**{discord.utils.escape_markdown(str(await self.bot.fetch_unknown_user(user)))}**\n"
                    + msg.content)

    @commands.command(brief="Lists all quotes", aliases=["luq"])
    async def listuserquotes(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        await ctx.paginate(
            (f"**#{row[0]}** - **{discord.utils.escape_markdown(row[1])}**"
             for row in await self.bot.db.conn.execute_fetchall("select id, name from quotes where user=? and guild=?",
                                                                (member.id, ctx.guild.id))),
            30,
            f"Quotes by {member}"
        )

    @commands.command(brief="Delete a quote", aliases=["delq"])
    async def deletequote(self, ctx: aoi.AoiContext, quote: int):
        qid, user, guild = (
            await (await self.bot.db.conn.execute("select id, user, guild from quotes where id=?",
                                                  (quote,))
                   ).fetchone())
        if user != ctx.author.id and not ctx.author.guild_permissions.administrator:
            return ctx.send_error("You must be administrator to delete quotes that aren't yours.")
        await self.bot.db.conn.execute("delete from quotes where id=?", (qid,))
        await self.bot.db.conn.commit()

    @commands.command(brief="Search quotes", aliases=["searchq"])
    async def searchquotes(self, ctx: aoi.AoiContext, *, search_term: str):
        rows = await self.bot.db.conn.execute_fetchall("select id, name from quotes where "
                                                       "guild=? and content like ?",
                                                       (ctx.guild.id, f"%{search_term}%"))
        await ctx.paginate(
            (f"**{row[0]}** - **{discord.utils.escape_markdown(row[1])}**"
             for row in rows),
            30,
            "Quote Search"
        )

    # TODO add list all by tag


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Quotes(bot))
