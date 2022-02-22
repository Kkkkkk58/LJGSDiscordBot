import re
import math
import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.command(
        name='help', aliases=['h', 'commands'], description="Помощь (аналоги - h, commands)"
    )
    async def help(self, ctx, cog="1"):
        helpEmbed = discord.Embed(
            title="Вот списочек моих команд", color=ctx.author.colour
        )
        helpEmbed.set_thumbnail(url=ctx.guild.me.avatar_url)
        helpEmbed.add_field(name = "Анекдоты", value = f"**joke** - *Рассказываю рандомный анекдот (аналог - anecdote)*\n")
        helpEmbed.add_field(name="Очистка", value=f"**clear** - *<кол-во сообщений(1-100)> - Удаляю выбранное количество сообщений (аналог - purge)*\n")
        helpEmbed.add_field(name="Помощь", value=f"**help** - *Помощь (аналоги - h, commands)*\n")
        helpEmbed.add_field(name="Музыка", value=f"**connect** - *Присоединяюсь к голосовому каналу, в котором находится пользователь; можно также прописать канал, к которому я должен присоединиться (аналог - join)*\n**disconnect** - *Отключаюсь от голосового канала (аналог - leave)*\n**play** - *Проигрываю песню по названию или прямой ссылке youtube или продолжаю воспроизведение после паузы*\n**pause** - *Ставлю воспроизведение на паузу*\n**stop** - *Останавливаю воспроизведение*\n**next** - *Перехожу к следующей песне (аналог - skip)*\n**previous** - *Проигрываю предыдущий трек*\n**shuffle** - *Перемешиваю плейлист*\n**repeat** - *<none|1|all> - Меняю тип повторения списка воспроизведения, где 1 - повтор одного трека, all - повтор всего плейлиста, none - отмена повтора*\n**queue** - *Отображаю текущую очередь воспроизведения*\n")



        await ctx.send(embed=helpEmbed)


def setup(bot):
    bot.add_cog(Help(bot))