from typing import Optional, override

import discord
from discord import app_commands
import wavelink
from discord.ext import commands
import asyncio
import datetime
import urllib.parse

# import the bot class from bot.py
from bot import CritBot
from Utils import GeniusLyrics, Paginator, SongNotFound
from enum import Enum
from typing import cast


class Platform(Enum):
    YOUTUBE = ("youtube", "yt")
    SPOTIFY = ("spotify", "sp")
    SOUNDCLOUD = ("soundcloud", "sc")
    YOUTUBE_MUSIC = ("youtube_music", "ytm")

    @classmethod
    def from_string(cls, value: str) -> "Platform":
        for platform in cls:
            if value.lower() in platform.value:
                return platform
        return cls.YOUTUBE  # default to Youtube if no match is found

    def __str__(self) -> str:
        return self.value[0]


class Music(commands.Cog):
    def __init__(self, bot: CritBot):
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

    @commands.Cog.listener()
    async def on_wavelink_node_ready(
        self, payload: wavelink.NodeReadyEventPayload
    ) -> None:
        self.log(
            20,
            f"Wavelink node <{payload.node.identifier}> ready! "
            f"({payload.node.players} players)",
        )

    @commands.Cog.listener()
    async def on_wavelink_track_start(
        self, payload: wavelink.TrackStartEventPayload
    ) -> None:
        self.log(20, f"Wavelink track <{payload.track.title}> started!")
        self.log(20, f"Original {payload.original.title}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        player: wavelink.Player = payload.player
        if player.queue:
            await asyncio.gather(
                player.play(await player.queue.get_wait()),
                player.ctx.send(f"A tocar agora: {payload.track.title}"),
            )
    
    @commands.Cog.listener()
    async def on_wavelink_extra_event(self, payload: wavelink.ExtraEventPayload) -> None:
        print(f"DATA: {payload.data}\nNODE: {payload.node}\nPLAYER: {payload.player}")
        

    @staticmethod
    async def send_reaction(ctx: commands.Context, msg: str) -> None:
        """This function sends a reaction if the it is a prefix command, or a message if it is a slash command.

        Args:
            ctx (commands.Context): The context of the command.
            msg (str): The message to send.
        """
        if ctx.message.content:
            await ctx.message.add_reaction(msg)
        else:
            await ctx.send(msg)

    @staticmethod
    def parse_duration(duration: float | int) -> str:
        value = str(datetime.timedelta(seconds=duration))
        if value.startswith("0:"):
            value = value[2:]
        return value

    async def ensure_voice(self, ctx: commands.Context) -> bool:
        """This function always ensures that the bot is in a voice channel.
        If the bot is not in a voice channel, it will join the voice channel.
        If the bot is in a voice channel, but the user is in a different voice channel, it will return False.

        Args:
            ctx (commands.Context): The context of the command.

        Returns:
            bool: If the bot is in the same voice channel as the user.
        """
        node = wavelink.Pool.get_node()

        await node.send(
            "PUT",
            path=f"v4/sessions/{node.session_id}/players/{ctx.guild.id}/sponsorblock/categories",
            data=[
                "sponsor",
                "selfpromo",
                # "interaction",
                "intro",
                "outro",
                # "preview",
                "music_offtopic",
                # "filler",
            ],
        )
        player = cast(wavelink.Player, ctx.voice_client)
        if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore
            await ctx.send(self.t("not_in_voice"))
            return False
        if player is not None and player.connected:
            if player.channel.id != ctx.author.voice.channel.id:  # type: ignore
                await ctx.send(self.t("not_in_same_voice"))
                return False
        else:
            await ctx.author.voice.channel.connect(self_deaf=True, cls=wavelink.Player)  # type: ignore
        return True

    @staticmethod
    def make_progress_bar(progress: int, total: int, length: int = 10) -> str:
        num_hash = int((progress / total) * length)
        return "⎯" * num_hash + ":radio_button:" + "⎯" * (length - num_hash - 1)

    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        if not await self.ensure_voice(ctx):
            return

        query = query.strip("<>")

        tracks: wavelink.Search = await wavelink.Playable.search(query)

        player = cast(wavelink.Player, ctx.voice_client)
        player.ctx = ctx

        if not tracks:
            await ctx.reply(self.t("err", "no_tracks_found", query=query))
            return

        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            await ctx.send(
                self.t("cmd", "queued_playlist", playlist=tracks.name, length=added)
            )
        else:

            await asyncio.gather(
                player.queue.put_wait(tracks[0]),
                ctx.send(
                    self.t(
                        "cmd", "queued", track=tracks[0].title, author=tracks[0].author
                    )
                ),
            )

        if not player.playing:
            await player.play(await player.queue.get_wait(), volume=30)

    @commands.hybrid_command(aliases=["s"])
    async def skip(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        await asyncio.gather(
            player.skip(force=True), self.send_reaction(ctx, "\u23ED\ufe0f")
        )

    @commands.hybrid_command(aliases=["pausa"])
    async def pause(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return
        if player.paused:
            await ctx.send(self.t("err", "already_paused"))
            return

        await asyncio.gather(player.pause(True), self.send_reaction(ctx, "⏸️"))

    @commands.hybrid_command(aliases=["r", "continua"])
    async def resume(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if player.paused:
            await asyncio.gather(player.pause(False), self.send_reaction(ctx, "⏭️"))
        else:
            await ctx.send(self.t("err", "not_paused"))

    @staticmethod
    def nice_filter_name(filter_name: str) -> str:
        if filter_name == "reverb":
            filter_name = "slowed + reverb"
        return filter_name.replace("_", " ").title()

    async def filter_show_logic(self, ctx: commands.Context) -> None:
        # list all filters
        if ctx.invoked_subcommand is None:
            filter_cmd_list = [cmd.name for cmd in self.bot.get_command("filter").commands]  # type: ignore
            embed = discord.Embed(
                title=self.t("embed", "title", mcommand_name="filter"),
                description=self.t("embed", "description", mcommand_name="filter"),
            )
            for fil in filter_cmd_list:
                if fil == "show":
                    continue
                embed.add_field(
                    name=self.nice_filter_name(fil),
                    value=fil
                    if fil != "clear"
                    else self.t("command_name", mcommand_name="filter_clear"),
                    inline=False,
                )
            await ctx.send(embed=embed)

    @commands.hybrid_group(aliases=["f", "filtro", "filtros", "filters"])
    async def filter(self, ctx: commands.Context) -> None:
        await self.filter_show_logic(ctx)

    @filter.command(name="show", aliases=["mostrar"])
    async def show(self, ctx: commands.Context) -> None:
        self.bot.i18n.command_name = "filter"
        await self.filter_show_logic(ctx)

    @filter.command(name="nightcore")
    async def nightcore(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        filters: wavelink.Filters = player.filters
        if (
            filters.timescale.payload.get("pitch") == 1.2
            and filters.timescale.payload.get("speed") == 1.2
            and filters.timescale.payload.get("rate") == 1
        ):
            filters.reset()
            await asyncio.gather(
                player.set_filters(filters, seek=True),
                ctx.send(self.t("cmd", "nightcore_off")),
            )
            return

        filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
        await asyncio.gather(
            player.set_filters(filters, seek=True), self.send_reaction(ctx, "\u2705")
        )

    @filter.command(name="bass_boost")
    async def bass_boost(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        filters: wavelink.Filters = player.filters
        if filters.equalizer.payload[0]["gain"] == 0.25:
            filters.reset()
            await asyncio.gather(
                player.set_filters(filters, seek=True),
                ctx.send(self.t("cmd", "bassboost_off")),
            )
            return

        # TODO improve this
        filters.equalizer.set(bands=[{"band": 0, "gain": 0.25}])

        await asyncio.gather(
            player.set_filters(filters, seek=True), self.send_reaction(ctx, "\u2705")
        )

    @filter.command(name="8d")
    async def eight_d(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        filters: wavelink.Filters = player.filters
        if (
            filters.timescale.payload.get("pitch") == 1.05
            and filters.rotation.payload.get("rotationHz") == 0.125
            and filters.tremolo.payload.get("depth") == 0.3
            and filters.tremolo.payload.get("frequency") == 14
            # and filters.equalizer.payload.get("1dB") == -0.2
        ):
            filters.reset()
            await asyncio.gather(
                player.set_filters(filters, seek=True),
                ctx.send(self.t("cmd", "8d_off")),
            )
            return

        filters.timescale.set(pitch=1.05)
        filters.tremolo.set(depth=0.3, frequency=14)
        filters.rotation.set(rotation_hz=0.125)
        filters.equalizer.set(bands=[{"band": 1, "gain": -0.2}])

        await asyncio.gather(
            player.set_filters(filters, seek=True), self.send_reaction(ctx, "\u2705")
        )

    # slowed + reverb
    @filter.command(name="reverb")
    async def reverb(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        filters: wavelink.Filters = player.filters
        if (
            filters.timescale.payload.get("pitch") == 0.8
            and filters.timescale.payload.get("rate") == 0.9
        ):
            filters.reset()
            await asyncio.gather(
                player.set_filters(filters, seek=True),
                ctx.send(self.t("cmd", "reverb_off")),
            )
            return

        filters.timescale.set(pitch=0.8, rate=0.9)

        await asyncio.gather(
            player.set_filters(filters, seek=True), self.send_reaction(ctx, "\u2705")
        )

    @filter.command(name="clear", aliases=["limpar"])
    async def clear(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        filters: wavelink.Filters = player.filters
        filters.reset()
        await asyncio.gather(
            player.set_filters(filters, seek=True), self.send_reaction(ctx, "\u2705")
        )

    @commands.hybrid_command(aliases=["t"])
    async def tts(self, ctx: commands.Context, *, text: str = None) -> None:
        if not text:
            await ctx.send(self.t("err", "no_text"))
            return
        # URI encode the text
        text = urllib.parse.quote(text)
        lang = self.bot.i18n.get_lang(ctx.guild.id)
        voice = "Carolina" if lang == "pt" else "Olivia"
        if not await self.ensure_voice(ctx):
            return

        player = cast(wavelink.Player, ctx.voice_client)
        tracks: wavelink.Search = await wavelink.Playable.search(
            "ftts://" + text + "?voice=" + voice
        )  # flower tts
        track = tracks[0]

        if not player.playing:
            await asyncio.gather(
                player.play(track, volume=100),
                self.send_reaction(ctx, "\u2705"),
            )
        else:
            await asyncio.gather(
                player.queue.put_wait(track),
                ctx.send(
                    self.t(
                        "cmd",
                        "queued",
                        track=track.title,
                        author=track.author,
                        mcommand_name="play",
                    )
                ),
            )

    @commands.hybrid_command()
    async def seek(self, ctx: commands.Context, secs: int) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        time = secs * 1000
        position = self.parse_duration(round(player.position / 1000))
        time_to_seek = self.parse_duration(secs)

        await asyncio.gather(
            player.seek(time),
            ctx.send(self.t("cmd", "output", position=position, time=time_to_seek)),
        )

    @commands.hybrid_command(
        aliases=["np", "nowplaying", "tocando", "current", "currentsong", "a_tocar"]
    )
    async def now_playing(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        track = player.current
        position = round(player.position / 1000)
        parsed_position = self.parse_duration(position)
        total = track.length
        parsed_length = self.parse_duration(total)
        progress_bar = self.make_progress_bar(position, total)

        embed = discord.Embed()
        embed.set_author(icon_url=ctx.author.avatar.url, name=self.t("embed", "title"))
        embed.add_field(
            name=self.t("embed", "currently_playing"),
            value=f"[{track.title}]({track.uri}) - *({parsed_length})*",
            inline=False,
        )

        embed.add_field(
            name=self.t("embed", "by"),
            value=f"[{track.author}]({track.artist.url})",
            inline=False,
        )
        embed.add_field(
            name="Likes",
            value=f"<:likeemoji:1074046790237700097> {"LIKES"}",
        )
        embed.add_field(
            name="Dislikes",
            value=f"<:dislikeemoji:1074052963649200198> {"DISLIKES"}",
        )
        embed.add_field(
            name=self.t("embed", "views"),
            value=f"<:views:1074047661759528990> {"VIEWS"}",
        )
        embed.add_field(
            name=self.t("embed", "subs"), value=f':envelope: {"SUBS"}'
        )
        embed.add_field(
            name=self.t("embed", "uploaded"),
            value=f":calendar_spiral: {"UPLOAD DATE"}",
            inline=False,
        )
        embed.add_field(
            name=self.t("embed", "requested_by"),
            value=f"{"REQUESTED"} {self.t('embed', 'ago', time=69)}",
            inline=False,
        )
        embed.add_field(
            name=self.t("embed", "progress"),
            value=f"{':arrow_forward:' if not player.paused else ':pause_button:'} {self.parse_duration(round(player.position))} - {progress_bar} - {self.parse_duration(track.length)}",
            inline=False,
        )
        volume_emoji = ":sound:" if player.volume <= 50 else ":loud_sound:"
        if player.volume == 0:
            volume_emoji = ":mute:"
        embed.add_field(name="Volume", value=f"{volume_emoji} {player.volume}%")
        # embed.add_field(
        #     name=self.t("embed", "next"),
        #     value=f":track_next: `{player.queue[0].info['title']} - {self.parse_duration(player.queue[0].duration)}`"
        #     if player.queue
        #     else self.t("embed", "no_next"),
        # )
        embed.timestamp = datetime.datetime.now()

        embed.set_thumbnail(url=track.artwork)
        await ctx.send(embed=embed)
    

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))


async def teardown(bot) -> None:
    await bot.remove_cog("Music")
