
from typing import Optional
from datetime import datetime, timedelta
from discord import Member
from discord.ext.commands import Cog, Greedy
from discord.ext.commands import command, has_permissions, bot_has_permissions


class Clear(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="clear", aliases=["purge"], description=" <кол-во сообщений(1-100)> - Удаляю выбранное количество сообщений (аналог - purge)")
    @bot_has_permissions(manage_messages=True)
    @has_permissions(manage_messages=True)
    async def clear_messages(self, ctx, targets: Greedy[Member], limit: Optional[int] = 1):
        def _check(message):
            return not len(targets) or message.author in targets
        if 0 < limit <= 100:
            with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(limit=limit, after=datetime.utcnow() - timedelta(days=14),
                                                  check=_check)
                await ctx.send(f"Как и просили, удалил вот столько сообщений: {len(deleted):,} ", delete_after=5)
        else:
            await ctx.send("Такие количества за пределами моих возможностей(((((( Я могу удалять от 1 до 100 сообщений")

def setup(bot):
    bot.add_cog(Clear(bot))
