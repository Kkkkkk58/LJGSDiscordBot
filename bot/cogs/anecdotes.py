import parse
from discord.ext import commands
from discord.ext.commands import Cog


class Anecdotes(Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="joke", aliases=["anecdote"], description="Рассказываю рандомный анекдот (аналог - anecdote)")
	async def anecdote_command(self, ctx):
		items = str(parse.parse()).replace('<div class="text">', '').replace('</div>', '').replace('<br/>', '\n')
		await ctx.send(items)


def setup(bot):
	bot.add_cog(Anecdotes(bot))
