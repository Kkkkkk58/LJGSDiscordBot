from discord import Forbidden
from discord.ext.commands import Cog
import asyncio


class Welcome(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_member_join(self, member):
		await self.bot.get_channel(758936062348492831).send(f"О, привет, {member.mention}! А я тебя знаю! Добро пожаловать на сервер **LJGS**!")
		try:
			await member.send(f"Добро пожаловать в **{member.guild.name}**! Будь как дома, путник")
		except Forbidden:
			pass
		await member.add_roles(member.guild.get_role(777953900342018050))

	@Cog.listener()
	async def on_member_remove(self, member):
		await self.bot.get_channel(758936062348492831).send(f"{member.display_name} ливнул. Чорт! Ну и катись.")


	@Cog.listener()
	async def on_guild_join(self, guild):
		await self.bot.get_channel(758936062348492831).send(f"О привет!")
		async with self.bot.get_channel(758936062348492831).typing():
			await asyncio.sleep(2)
		await self.bot.get_channel(758936062348492831).send(f"А я вас знаю!")
		async with self.bot.get_channel(758936062348492831).typing():
			await asyncio.sleep(2)
		await self.bot.get_channel(758936062348492831).send(f"Вы же друзья и знакомые **LJGS**")
		async with self.bot.get_channel(758936062348492831).typing():
			await  asyncio.sleep(2)
		await self.bot.get_channel(758936062348492831).send("<@!252794467885645826> - мой батя, и он создал меня чтобы заменить всех ненужных кинчеботов")
		async with self.bot.get_channel(758936062348492831).typing():
			await  asyncio.sleep(2)
		await self.bot.get_channel(758936062348492831).send(f"Я могу стать вашим диджеем, чистильщиком, а еще умею рассказывать анекдоты!")
		async with self.bot.get_channel(758936062348492831).typing():
			await  asyncio.sleep(2)
		await self.bot.get_channel(758936062348492831).send(f"И при этом я не буду вас бесить тем, что отвечаю Б, когда вы говорите а")
		await self.bot.get_channel(758936062348492831).send(f"а")
		async with self.bot.get_channel(758936062348492831).typing():
			await  asyncio.sleep(1)
		await self.bot.get_channel(758936062348492831).send("<@!724606799180857375>, кстати, ты уволен.")
		async with self.bot.get_channel(758936062348492831).typing():
			await  asyncio.sleep(2)
		await self.bot.get_channel(758936062348492831).send(f"Ну вопщемта всем привет, надеюсь на ваше гостеприимство 🥰")
		await self.bot.get_channel(758936062348492831).send(f"Кстати, в статусе должно быть написано, но, если что, мой префикс - ljgs!")


def setup(bot):
	bot.add_cog(Welcome(bot))
