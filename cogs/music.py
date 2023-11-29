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

        self.play_cmd = app_commands.Command(
            name="play",
            description="command_description",
            callback=self.play_app_command,
            extras={
                "cog_name": "music",
                "command_name": "play",
            },
        )
        self.bot.tree.add_command(self.play_cmd)

        self.genius = GeniusLyrics(self.bot.genius_token, self.bot.web_client)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        self.log(20, f"Node <{node.id}> is ready!")

    async def _play_logic(
        self, ctx: commands.Context, query: str, platform: Platform
    ) -> None:
        vc: wavelink.Player = await self.join_logic(
            ctx, channel=ctx.author.voice.channel, play=True
        )
        query = query.strip("<>")

        print(f"Query: {query}")
        print(f"Platform: {platform}")

        # do things...

    async def play_app_command(
        self,
        interaction: discord.Interaction,
        platform: Optional[Platform],
        *,
        query: str,
    ) -> None:
        await interaction.response.defer()
        await self._play_logic(
            await self.bot.get_context(interaction), query, platform or Platform.YOUTUBE
        )

    @commands.command(aliases=["p"])
    async def play(
        self,
        ctx: commands.Context,
        *,
        query: str,
    ) -> None:
        arg = query
        platform = None

        for p in Platform:
            if (first := arg.split(" ")[0]) in p.value:
                platform = p
                query = arg[len(first) + 1 :]
                break

        platform = platform or Platform.YOUTUBE

        await self._play_logic(ctx, query, platform)

    async def join_logic(
        self,
        ctx: commands.Context,
        channel: Optional[discord.VoiceChannel] = None,
        play: bool = False,
    ) -> None | wavelink.Player:
        if not channel and not ctx.author.voice:
            await ctx.send(self.t("err", "not_in_voice", mcommand_name="join"))
            return None

        channel = channel or ctx.author.voice.channel
        vc: wavelink.Player = ctx.voice_client

        if vc and vc.is_connected() and vc.channel != channel:
            await asyncio.gather(
                vc.move_to(channel),
                ctx.send(
                    self.t("cmd", "connect", channel=channel, mcommand_name="join")
                ),
            )
            return vc

        elif not vc:
            vc, _ = await asyncio.gather(
                channel.connect(cls=wavelink.Player, self_deaf=True),
                ctx.send(
                    self.t("cmd", "connect", channel=channel, mcommand_name="join")
                ),
            )
            return vc

        elif vc.is_connected() and vc.channel == channel:
            if not play:
                await ctx.send(self.t("err", "already_connected", mcommand_name="join"))
            return vc

    @commands.hybrid_command(aliases=["j", "entra"])
    async def join(
        self, ctx: commands.Context, *, channel: Optional[discord.VoiceChannel] = None
    ) -> None:
        await self.join_logic(ctx, channel=channel)

    @commands.hybrid_command(aliases=["l", "sai"])
    async def leave(self, ctx: commands.Context) -> None:
        vc: wavelink.Player = ctx.voice_client
        if not vc:
            await ctx.send(self.t("err", "not_connected"))
            return

        await asyncio.gather(
            vc.disconnect(),
            ctx.message.add_reaction("👋"),
        )

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))


async def teardown(bot) -> None:
    await bot.remove_cog("Music")
