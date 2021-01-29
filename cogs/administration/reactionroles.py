from dataclasses import dataclass
from typing import Dict, Optional, List, Union

import aoi
import discord
from aoi import AoiDatabase
from discord.ext import commands
from libs.converters import partial_emoji_convert


@dataclass()
class _ReactionRoleData:
    role: discord.Role


class ReactionRoles(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self._roles: Dict[int, Dict[str, _ReactionRoleData]] = {}
        self._reaction_cache: Dict[int, Dict[str, List[int]]] = {}
        self._db: Optional[AoiDatabase]
        self.bot.loop.create_task(self._init())

    async def _delete(self, row):
        await self._db.db.execute("delete from rero where rowid=?", (row[0],))

    async def _init(self):
        self.bot.logger.info("rero:Waiting for bot")
        await self.bot.wait_until_ready()
        self._db = self.bot.db
        for row in await self._db.db.execute_fetchall("select rowid, * from rero"):
            channel: discord.TextChannel = self.bot.get_channel(row[2])
            if not channel:
                await self._delete(row)
                continue
            message_id: int = row[3]
            if message_id not in self._roles:
                try:
                    await channel.fetch_message(message_id)
                except discord.NotFound:
                    await self._delete(row)
                    continue
            role: discord.Role = self.bot.get_guild(row[1]).get_role(row[5])
            if not role:
                await self._delete(row)
                continue
            emoji_name: str = row[4]
            if message_id not in self._roles:
                self._roles[message_id] = {}
            self._roles[message_id][emoji_name] = _ReactionRoleData(role)
        await self._db.db.commit()
        self.bot.logger.info("rero:Ready!")

    @property
    def description(self):
        return "Commands to manage reaction roles"

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self._roles:
            return
        if str(payload.emoji.id) in self._roles[payload.message_id]:
            role = self._roles[payload.message_id][str(payload.emoji.id)].role
            if role:
                await payload.member.add_roles(role)
            return
        if payload.emoji.name in self._roles[payload.message_id]:
            role = self._roles[payload.message_id][str(payload.emoji.name)].role
            if role:
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id not in self._roles:
            return
        if self._emoji(payload.emoji) in self._roles[payload.message_id]:
            # inject payload member
            # come on discord, why not just tell us who un-reacted :(
            payload.member = self.bot.get_guild(payload.guild_id).get_member(payload.user_id)
            if payload.message_id not in self._roles:
                return
            if str(payload.emoji.id) in self._roles[payload.message_id]:
                role = self._roles[payload.message_id][str(payload.emoji.id)].role
                if role:
                    await payload.member.remove_roles(role)
                return
            if payload.emoji.name in self._roles[payload.message_id]:
                role = self._roles[payload.message_id][str(payload.emoji.name)].role
                if role:
                    await payload.member.remove_roles(role)

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Add a reaction role message")
    async def addrero(self, ctx: aoi.AoiContext, message: discord.Message, *, args: str):
        split = ctx.group_list(args.split(), 2)
        role_converter = commands.RoleConverter()
        for i in split:
            print(i)
            try:
                emoji: discord.PartialEmoji = await partial_emoji_convert(ctx, i[0])
                role: discord.Role = await role_converter.convert(ctx, i[1])
            except commands.PartialEmojiConversionFailure:
                return await ctx.send_error(f"Emoji {i[0]} invalid")
            except commands.RoleNotFound:
                return await ctx.send_error(f"Role {i[1]} invalid")
            try:
                await message.add_reaction(emoji)
            except discord.Forbidden:
                return await ctx.send_error("I can't react to that message!")
            except discord.HTTPException:
                return await ctx.send_error(f"Emoji {i[0]} invalid")
            if message.id not in self._roles:
                self._roles[message.id] = {}
            if emoji.name in self._roles[message.id] or str(emoji.id) in self._roles[message.id]:
                return await ctx.send_error("That emoji is already being used")
            self._roles[message.id][str(emoji.id) if emoji.id else emoji.name] = _ReactionRoleData(role)
            await self._db.db.execute("insert into rero values (?,?,?,?,?,0,0)",
                                      (ctx.guild.id, message.channel.id, message.id,
                                       str(emoji.id) if emoji.id else emoji.name, role.id))
            await self._db.db.commit()
            await ctx.send_ok("Added!")

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Clear reaction roles from a message")
    async def clearrero(self, ctx: aoi.AoiContext, message: discord.Message, emoji: str = None):
        if message.id not in self._roles:
            return await ctx.send_error("Message has no reaction roles!")
        if not emoji:
            await message.clear_reactions()
            del self._roles[message.id]
            await self._db.db.execute("delete from rero where message=?", (message.id,))
            await self._db.db.commit()
            return await ctx.send_ok("Cleared all reaction roles from message")
        emoji = await partial_emoji_convert(ctx, emoji)
        if self._emoji(emoji) not in self._roles[message.id]:
            return await ctx.send_error(f"{emoji} not part of the reaction role")
        del self._roles[message.id][self._emoji(emoji)]
        await self._db.db.execute("delete from rero where message=? and emoji=?", (message.id, self._emoji(emoji)))
        await self._db.db.commit()
        return await ctx.send_ok(f"Cleared {self._emoji(emoji)}")

    def _emoji(self, emoji: Union[str, discord.PartialEmoji]):
        if isinstance(emoji, str):
            return emoji
        return str(emoji.id) if emoji.id else emoji.name


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(ReactionRoles(bot))
