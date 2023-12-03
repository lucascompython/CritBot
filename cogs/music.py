from typing import Optional

import discord
from discord import app_commands
import wavelink
from discord.ext import commands
import asyncio

# import the bot class from bot.py
from bot import CritBot
from Utils import GeniusLyrics, Paginator, SongNotFound
from enum import Enum


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

    async def ensure_voice(self, ctx: commands.Context) -> bool:
        """This function always ensures that the bot is in a voice channel.
        If the bot is not in a voice channel, it will join the voice channel.
        If the bot is in a voice channel, but the user is in a different voice channel, it will return False.

        Args:
            ctx (commands.Context): The context of the command.

        Returns:
            bool: If the bot is in the same voice channel as the user.
        """

        player: wavelink.Player = ctx.voice_client
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(self.t("not_in_voice"))
            return False
        if player is not None and player.connected:
            if player.channel.id != ctx.author.voice.channel.id:
                await ctx.send(self.t("not_in_same_voice"))
                return False
        else:
            await ctx.author.voice.channel.connect(self_deaf=True, cls=wavelink.Player)
        return True

    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        if not await self.ensure_voice(ctx):
            return

        query = query.strip("<>")

        tracks: wavelink.Search = await wavelink.Playable.search(query)

        player: wavelink.Player = ctx.voice_client

        if not tracks:
            await ctx.reply(self.t("cmd", "no_tracks_found", query=query))
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

    @staticmethod
    def nice_filter_name(filter_name: str) -> str:
        if filter_name == "reverb":
            filter_name = "slowed + reverb"
        return filter_name.replace("_", " ").title()

    @commands.hybrid_group(aliases=["f", "filtro"])
    async def filter(self, ctx: commands.Context) -> None:
        # list all filters
        if ctx.invoked_subcommand is None:
            filter_cmd_list = [cmd.name for cmd in ctx.command.commands]
            embed = discord.Embed(
                title=self.t("embed", "title"),
                description=self.t("embed", "description"),
            )
            for fil in filter_cmd_list:
                embed.add_field(
                    name=self.nice_filter_name(fil),
                    value=fil
                    if fil != "clear"
                    else self.t("command_name", mcommand_name="filter_clear"),
                    inline=False,
                )
            await ctx.send(embed=embed)

    @filter.command(name="nightcore")
    async def nightcore(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
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
            player.set_filters(filters, seek=True), ctx.message.add_reaction("\u2705")
        )

    @filter.command(name="bass_boost")
    async def bass_boost(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
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
            player.set_filters(filters, seek=True), ctx.message.add_reaction("\u2705")
        )

    @filter.command(name="8d")
    async def eight_d(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
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
            player.set_filters(filters, seek=True), ctx.message.add_reaction("\u2705")
        )

    # slowed + reverb
    @filter.command(name="reverb")
    async def reverb(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
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
            player.set_filters(filters, seek=True), ctx.message.add_reaction("\u2705")
        )

    @filter.command(name="clear", aliases=["limpar"])
    async def clear(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        filters: wavelink.Filters = player.filters
        filters.reset()
        await asyncio.gather(
            player.set_filters(filters, seek=True), ctx.message.add_reaction("\u2705")
        )

    @commands.hybrid_command(aliases=["pausa"])
    async def pause(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return
        if player.paused:
            await ctx.send(self.t("err", "already_paused"))
            return

        await asyncio.gather(player.pause(True), ctx.message.add_reaction("⏸️"))

    @commands.hybrid_command(aliases=["continua"])
    async def resume(self, ctx: commands.Context) -> None:
        player: wavelink.Player = ctx.voice_client
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if player.paused:
            await asyncio.gather(player.pause(False), ctx.message.add_reaction("⏭️"))
        else:
            await ctx.send(self.t("err", "not_paused"))

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))


async def teardown(bot) -> None:
    await bot.remove_cog("Music")
