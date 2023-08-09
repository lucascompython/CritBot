from typing import Optional

import discord
import wavelink
from discord.ext import commands
import asyncio

# import the bot class from bot.py
from bot import CritBot
from Utils import GeniusLyrics, Paginator, SongNotFound


class Music(commands.Cog):
    def __init__(self, bot: CritBot):
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

        self.genius = GeniusLyrics(self.bot.genius_token, self.bot.web_client)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        self.log(20, f"Node <{node.id}> is ready!")

    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        vc: wavelink.Player = await self.join_logic(
            ctx, channel=ctx.author.voice.channel, play=True
        )

        query = query.strip("<>")
        print(query)

        track = await wavelink.Playable.search(query)
        print(track)

        await vc.play(track[0])

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
    ) -> None | wavelink.Player:
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
