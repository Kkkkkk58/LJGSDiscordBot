import discord
import wavelink
from discord.ext import commands
import typing as t
import random
import asyncio
import datetime as dt
import re
from enum import Enum

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}

class AlreadyConnectedToChannel(commands.CommandError):
    pass

class NoVoiceChannel(commands.CommandError):
    pass

class QueueIsEmpty(commands.CommandError):
    pass

class NoTracksFound(commands.CommandError):
    pass

class PlayerIsAlreadyPaused(commands.CommandError):
    pass

class NoMoreTracks(commands.CommandError):
    pass

class NoPreviousTracks(commands.CommandError):
    pass

class InvalidRepeatMode(commands.CommandError):
    pass

class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2

class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty
        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty
        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty
        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty
        self.position += 1
        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None
        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty
        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "1":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "all":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel
        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel
        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound
        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            await ctx.send(f"✅ {tracks[0].title} добавлена в очередь")
        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                self.queue.add(track)
                await ctx.send(f"✅ {track.title} добавлена в очередь")
        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                    r.emoji in OPTIONS.keys()
                    and u == ctx.author
                    and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="Выбери песню из списка",
            description=(
                "\n".join(
                    f"**{i + 1}.** {t.title} ({t.length // 60000}:{str(t.length % 60).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Результаты поиска")
        embed.set_footer(text=f"Запросил {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)



class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f" Wavelink node `{node.identifier}` ready.")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Эм ну музыка только в групповых чатах доступна")
            return False
        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        nodes = {
            "MAIN": {
                "host": "ljgs-bot.herokuapp.com",
                "port": 80,
                "rest_uri": "https://ljgs-bot.herokuapp.com/",
                "password": "youshallnotpass",
                "identifier": "MAIN",
                "region": "russia"
            }
        }
        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command(name="connect", aliases=["join"], description="Присоединяюсь к голосовому каналу, в котором находится пользователь; можно также прописать канал, к которому я должен присоединиться (аналог - join)")
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.send(f"Я подключился к каналу {channel.name}")

    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            await ctx.send("Я уже в канале так-то")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("Я не нашёл себе подходящего канала")

    @commands.command(name="disconnect", aliases=["leave"], description="Отключаюсь от голосового канала (аналог - leave)")
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.send("Ок, я ухожу")

    @commands.command(name="play", description="Проигрываю песню по названию или прямой ссылке youtube или продолжаю воспроизведение после паузы")
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)
        if query is None:
            if player.queue.is_empty:
                raise QueueIsEmpty
            await player.set_pause(False)
            await ctx.send("✅ Продолжаем!")
        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"
            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play_command.error
    async def play_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Так тут проигрывать нечего")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("Я не нашёл себе подходящего канала")

    @commands.command(name="pause", description="Ставлю воспроизведение на паузу")
    async def pause_command(self, ctx):
        player = self.get_player(ctx)
        if player.is_paused:
            raise PlayerIsAlreadyPaused
        await player.set_pause(True)
        await ctx.send("⏸Пауза")

    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Я и так на паузе....")

    @commands.command(name="stop", description="Останавливаю воспроизведение")
    async def stop_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.send("⏹Недолго музыка играла..")

    @commands.command(name="next", aliases=["skip"], description="Перехожу к следующей песне (аналог - skip)")
    async def next_command(self, ctx):
        player = self.get_player(ctx)
        if not player.queue.upcoming:
            raise NoMoreTracks
        await player.stop()
        await ctx.send("⏭Идём по некселю получается")

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Очередь пустая вообще-то")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("А всё, песенки закончились в очереди, дальше нет ничего")

    @commands.command(name="previous", description="Проигрываю предыдущий трек")
    async def previous_command(self, ctx):
        player = self.get_player(ctx)
        if not player.queue.history:
            raise NoPreviousTracks
        player.queue.position -= 2
        await player.stop()
        await ctx.send("⏮Я как Кристофер Нолан😎")

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Очередь пуста блин")
        elif isinstance(exc, NoPreviousTracks):
            await ctx.send("Предыдущих треков нет")

    @commands.command(name="shuffle", description="Перемешиваю плейлист")
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.shuffle()
        await ctx.send("🔀Перемешал")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Ну и как я должен перемешать пустую очередь?!")

    @commands.command(name="repeat", description=f"<none|1|all> - Меняю тип повторения списка воспроизведения, где 1 - повтор одного трека, all - повтор всего плейлиста, none - отмена повтора")
    async def repeat_command(self, ctx, mode: str):
        if mode not in ("none", "1", "all"):
            raise InvalidRepeatMode

        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        await ctx.send(f"Тип повтора - {mode}.")

    @commands.command(name="queue", description="Отображаю текущую очередь воспроизведения")
    async def queue_command(self, ctx, show: t.Optional[int] = 10):
        player = self.get_player(ctx)
        if player.queue.is_empty:
            raise QueueIsEmpty
        embed = discord.Embed(
            title="Очередь воспроизведения",
            description=f"Показывается до {show} треков",
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="🎶 МУЗЫКА 🎶")
        embed.set_footer(text=f"Спросил {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(
            name="Сейчас играет",
            value=getattr(player.queue.current_track, "title", "Ну, сейчас ничего не играет"),
            inline=False
        )
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name="А потом будет играть вот это",
                value="\n".join(t.title for t in upcoming[:show]),
                inline=False
            )
        msg = await ctx.send(embed=embed)

    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("Очередь пустая так-то. Обидно, да???😢😢😢")


def setup(bot):
    bot.add_cog(Music(bot))