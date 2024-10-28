import asyncio
import datetime
import os
import urllib.parse
from typing import Optional, cast

import aiofiles.os
import discord
import orjson
import wavelink
from discord import app_commands
from discord.ext import commands
from yt_dlp import YoutubeDL
from yt_dlp.utils import ExtractorError

# import the bot class from bot.py
from bot import CritBot
from Utils import BoolConverter, GeniusLyrics, Paginator, SongNotFound, SpotifyTrackInfo


class Music(commands.Cog):
    def __init__(self, bot: CritBot):
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        self.ytdlp_download_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/%(title)s.%(ext)s",
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }
        self.ytdlp_extract_info_opts = {
            "quiet": True,
            "skip_download": True,
        }

        self.ytdlp_extract = YoutubeDL(self.ytdlp_extract_info_opts)
        self.ytdlp_download = YoutubeDL(self.ytdlp_download_opts)
        self.SpotifyTrackInfo = SpotifyTrackInfo(self.bot.web_client)

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
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        self.bot.create_task(player.disconnect())

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, payload: wavelink.TrackEndEventPayload
    ) -> None:
        player: wavelink.Player = payload.player
        if player is None:
            return

        if player.queue and player.autoplay == wavelink.AutoPlayMode.disabled:
            track = player.queue.get()
            self.bot.create_task(player.play(track))
            if (
                track.source != "flowery-tts" and not track.first_playing
            ):  # the info message is already sent if the track is the first one and it's not a tts track
                self.bot.create_task(self.send_info_message(player.ctx, track))

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        _before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        player = cast(wavelink.Player, member.guild.voice_client)
        if player is None:
            return

        if after.channel != player.channel and member.id != self.bot.user.id:
            real_members = 0
            for m in player.channel.members:
                if not m.bot:
                    real_members += 1
            if real_members == 0:
                player.inactive_timeout = 300

        elif after.channel == player.channel:
            player.inactive_timeout = 0  # disable the inactive timeout so that while there is someone in the voice channel the bot won't disconnect

    @commands.Cog.listener()
    async def on_wavelink_extra_event(
        self, payload: wavelink.ExtraEventPayload
    ) -> None:
        if payload.data.get("type", "") == "SegmentSkipped":
            if self.bot.sponsorblock_cache[
                int(payload.data["guildId"])
            ].print_segment_skipped:
                await payload.player.ctx.send(
                    self.t(
                        "cmd",
                        "output",
                        category=payload.data["segment"]["category"]
                        .replace("_", " ")
                        .title(),
                        start=self.parse_duration(payload.data["segment"]["start"]),
                        end=self.parse_duration(payload.data["segment"]["end"]),
                        mcommand_name="sponsorblock_segment_skipped",
                    )
                )

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
        """Converts a duration in seconds to a human readable format.

        Args:
            duration (float | int): The duration in milliseconds.

        Returns:
            str: The duration in a human readable format.
        """
        value = str(datetime.timedelta(milliseconds=duration)).split(".")[0]
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

        player = cast(wavelink.Player, ctx.voice_client)
        if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore
            await ctx.send(self.t("not_in_voice"))
            return False
        if player is not None and player.connected:
            if player.channel.id != ctx.author.voice.channel.id:  # type: ignore
                await ctx.send(self.t("not_in_same_voice"))
                return False
        else:
            await asyncio.gather(
                ctx.author.voice.channel.connect(self_deaf=True, cls=wavelink.Player),  # type: ignore
                ctx.send(
                    self.t(
                        "cmd",
                        "connect",
                        channel=ctx.author.voice.channel,
                        mcommand_name="join",
                    )
                ),  # type: ignore
            )

            await self.bot.wavelink_node.send(
                "PUT",
                path=f"v4/sessions/{self.bot.wavelink_node.session_id}/players/{ctx.guild.id}/sponsorblock/categories",
                data=self.bot.sponsorblock_cache[ctx.guild.id].active_categories,
            )
        return True

    @staticmethod
    def make_progress_bar(progress: int, total: int, length: int = 10) -> str:
        num_hash = int((progress / total) * length)
        return "⎯" * num_hash + ":radio_button:" + "⎯" * (length - num_hash - 1)

    @staticmethod
    def put_playlist_at_beginning(
        player: wavelink.Player, playlist: wavelink.Playlist
    ) -> None:
        length = len(playlist)

        for i in range(length - 1, -1, -1):
            player.queue.put_at(0, playlist[i])

    @staticmethod
    def human_format(num: int) -> str:
        if not isinstance(num, int):
            return num

        suffixes = ("", "K", "M", "B", "T")
        magnitude = 0
        while abs(num) >= 1000 and magnitude < len(suffixes) - 1:
            magnitude += 1
            num /= 1000.0
        return f"{num:.3g}{suffixes[magnitude]}"

    async def get_dislikes(self, identifier: str) -> int:
        """This function already assumes this a youtube track.

        Args:
            track (wavelink.Playable): The youtube track

        Returns:
            str: The number of dislikes
        """
        async with self.bot.web_client.get(
            f"https://returnyoutubedislikeapi.com/votes?videoId={identifier}"
        ) as resp:
            dislikes = await resp.json(loads=orjson.loads)
            return dislikes["dislikes"]

    async def get_track_info(self, track: wavelink.Playable) -> dict[str, str] | None:
        match track.source:
            case "youtube":
                dislikes_task = self.bot.loop.create_task(
                    self.get_dislikes(track.identifier)
                )
                info = await self.bot.loop.run_in_executor(
                    None, self.ytdlp_extract.extract_info, track.identifier, False
                )

                view_count = self.human_format(info.get("view_count", "N/A"))
                like_count = self.human_format(info.get("like_count", "N/A"))
                subs = self.human_format(info.get("channel_follower_count", "N/A"))
                uploader_url = info.get("uploader_url", "N/A")
                date = info.get("upload_date", "N/A")
                if date != "N/A":
                    upload_date = f"{date[6:8]}-{date[4:6]}-{date[:4]}"

                dislikes = await dislikes_task

                return {
                    "view_count": view_count,
                    "like_count": like_count,
                    "dislike_count": self.human_format(dislikes),
                    "subs": subs,
                    "release_date": upload_date,
                    "uploader_url": uploader_url,
                }
            case "spotify":
                (
                    monthly_listeners,
                    playcount,
                    release_date,
                    explicit,
                ) = await self.SpotifyTrackInfo.get_info(
                    track.artist.url[-22:], track.identifier
                )

                return {
                    "monthly_listeners": monthly_listeners,
                    "playcount": self.human_format(int(playcount)),
                    "release_date": release_date,
                    "explicit": explicit,
                }
            case "soundcloud":
                info = await self.bot.loop.run_in_executor(
                    None, self.ytdlp_extract.extract_info, track.uri, False
                )

                playcount = self.human_format(info.get("view_count", "N/A"))
                likes = self.human_format(info.get("like_count", "N/A"))
                reposts = self.human_format(info.get("repost_count", "N/A"))
                uploader_url = info.get("uploader_url", "N/A")
                release_date = info.get("upload_date", "N/A")
                release_date = (
                    f"{release_date[6:8]}-{release_date[4:6]}-{release_date[:4]}"
                )

                return {
                    "playcount": playcount,
                    "likes": likes,
                    "reposts": reposts,
                    "release_date": release_date,
                    "uploader_url": uploader_url,
                }

            case _:
                return None

    async def send_info_message(
        self, ctx: commands.Context, track: wavelink.Playable
    ) -> None:
        info = await self.get_track_info(track)

        if track.source == "flowery-tts":
            self.bot.create_task(
                ctx.send(
                    self.t(
                        "cmd",
                        "now_playing",
                        track=track.title,
                        author=track.author,
                        mcog_name="music",
                        mcommand_name="play",
                    )
                )
            )
            return

        track_length = self.parse_duration(track.length)
        embed = discord.Embed(
            title=self.t(
                "embed",
                "title",
                source=track.source.capitalize(),
                description=f"```{track.title}```",
                mcog_name="music",
                mcommand_name="play",
            )
        )
        embed.set_thumbnail(url=track.artwork)
        embed.set_author(
            name=self.t(
                "embed",
                "author",
                user=track.ctx.author.name,
                mcog_name="music",
                mcommand_name="play",
            ),
            icon_url=track.ctx.author.avatar.url,
        )
        if info:
            embed.set_footer(
                text=self.t(
                    "embed",
                    "footer",
                    upload_date=info.get("release_date", "N/A"),
                    mcog_name="music",
                    mcommand_name="play",
                )
            )
        embed.add_field(
            name=self.t("embed", "duration", mcog_name="music", mcommand_name="play"),
            value=track_length,
        )

        if track.source == "youtube" or track.source == "soundcloud":
            track.artist.url = info[
                "uploader_url"
            ]  # for some reason lavalink doesn't set the artist url

        embed.add_field(
            name=self.t("embed", "artist", mcog_name="music", mcommand_name="play"),
            value=f"[{track.author}]({track.artist.url})"
            if track.artist.url
            else track.author,
        )
        embed.add_field(
            name="URL",
            value=self.t(
                "embed", "click", url=track.uri, mcog_name="music", mcommand_name="play"
            ),
        )
        match track.source:
            case "youtube":
                embed.add_field(
                    name=self.t(
                        "embed", "views", mcog_name="music", mcommand_name="play"
                    ),
                    value=info["view_count"],
                )
                embed.add_field(
                    name="Likes / Dislikes",
                    value=f"{info["like_count"]} 👍 / {info["dislike_count"]} 👎",
                )
                embed.add_field(
                    name=self.t(
                        "embed", "subs", mcog_name="music", mcommand_name="play"
                    ),
                    value=info["subs"],
                )
            case "spotify":
                embed.add_field(
                    name=self.t(
                        "embed",
                        "monthly_listeners",
                        mcog_name="music",
                        mcommand_name="play",
                    ),
                    value=info["monthly_listeners"],
                )
                embed.add_field(
                    name=self.t(
                        "embed", "playcount", mcog_name="music", mcommand_name="play"
                    ),
                    value=info["playcount"],
                )
                embed.add_field(
                    name=self.t(
                        "embed", "explicit", mcog_name="music", mcommand_name="play"
                    ),
                    value=self.t(
                        "embed", "yes", mcog_name="music", mcommand_name="play"
                    )
                    if info["explicit"]
                    else self.t("embed", "no", mcog_name="music", mcommand_name="play"),
                )
            case "soundcloud":
                embed.add_field(
                    name=self.t(
                        "embed", "playcount", mcog_name="music", mcommand_name="play"
                    ),
                    value=info["playcount"],
                )
                embed.add_field(
                    name="Likes",
                    value=info["likes"],
                )
                embed.add_field(
                    name=self.t(
                        "embed", "reposts", mcog_name="music", mcommand_name="play"
                    ),
                    value=info["reposts"],
                )

        self.bot.create_task(ctx.send(embed=embed))

    async def play_logic(
        self, ctx: commands.Context, query: str, play_next: bool
    ) -> None:
        if not await self.ensure_voice(ctx):
            return

        query = query.strip("<>")

        tracks: wavelink.Search = await wavelink.Playable.search(query)

        player = cast(wavelink.Player, ctx.voice_client)
        player.ctx = ctx

        if not tracks:
            self.bot.create_task(
                ctx.reply(self.t("err", "no_tracks_found", query=query))
            )
            return

        if isinstance(tracks, wavelink.Playlist):
            self.bot.create_task(
                ctx.send(
                    self.t(
                        "cmd",
                        "queued_playlist",
                        playlist=tracks.name,
                        length=len(tracks),
                    )
                )
            )
            for track in tracks:
                track.ctx = ctx
                track.first_playing = False

            if not player.playing:
                tracks[0].first_playing = True
                self.bot.create_task(player.play(tracks[0], volume=30))
                self.bot.create_task(player.queue.put_wait(tracks[1:]))
                self.bot.create_task(self.send_info_message(ctx, tracks[0]))

            else:
                if play_next:
                    self.put_playlist_at_beginning(player, tracks)
                else:
                    self.bot.create_task(player.queue.put_wait(tracks))

        else:
            tracks[0].ctx = ctx
            tracks[0].first_playing = not player.playing
            if not player.playing:
                self.bot.create_task(player.play(tracks[0], volume=30))
                self.bot.create_task(self.send_info_message(ctx, tracks[0]))
            else:
                self.bot.create_task(
                    ctx.send(
                        self.t(
                            "cmd",
                            "queued",
                            track=tracks[0].title,
                            author=tracks[0].author,
                        )
                    )
                )
                if play_next:
                    player.queue.put_at(0, tracks[0])
                else:
                    self.bot.create_task(
                        player.queue.put_wait(tracks[0]),
                    )

    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        await self.play_logic(ctx, query, False)

    @commands.hybrid_command(aliases=["pn"])
    async def play_next(self, ctx: commands.Context, *, query: str) -> None:
        self.bot.i18n.command_name = "play"  # use the play command translations
        await self.play_logic(ctx, query, True)

    @commands.hybrid_command(aliases=["autoplay", "ap"])
    async def auto_play(
        self, ctx: commands.Context, value: Optional[BoolConverter] = None
    ) -> None:
        if not await self.ensure_voice(ctx):
            return

        player = cast(wavelink.Player, ctx.voice_client)

        if value is None:
            status = ""
            if player.autoplay == wavelink.AutoPlayMode.disabled:
                status = self.t("cmd", "status_disabled")
            elif player.autoplay == wavelink.AutoPlayMode.enabled:
                status = self.t("cmd", "status_enabled")

            await ctx.send(self.t("cmd", "auto_play", status=status))

        elif value:
            player.autoplay = wavelink.AutoPlayMode.enabled
            await ctx.send(self.t("cmd", "enabled"))
            if not player.playing and (player.queue or player.auto_queue):
                await player.play(player.queue.get(), volume=30)
        else:
            player.autoplay = wavelink.AutoPlayMode.disabled
            await ctx.send(self.t("cmd", "disabled"))

    def _estimate_time_until(
        self, track: wavelink.Playable, player: wavelink.Player
    ) -> str:
        """Get the estimated until the given track is played.

        Args:
            track (wavelink.Playable): The track to estimate the time until.
            player (wavelink.Player): The player to get the current position.

        Returns:
            str: The estimated time until the track is played.
        """

        track_index = player.queue.index(track)
        total_time = 0
        for i in range(track_index):
            if player.queue[i].is_stream:
                total_time += 0
            else:
                total_time += player.queue[i].length

        if player.playing:
            total_time += player.current.length - player.position

        return self.parse_duration(total_time)

    @commands.hybrid_command(aliases=["q", "fila"])
    async def queue(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            self.bot.create_task(ctx.reply(self.t("not_in_voice")))
            return
        if not player.playing:
            self.bot.create_task(ctx.reply(self.t("not_playing")))
            return

        if len(player.queue) == 0:
            embed = discord.Embed(
                description=self.t(
                    "embed",
                    "description",
                    track=player.current.title,
                    user=player.current.ctx.author,
                    current_time=self.parse_duration(player.position),
                    total_time=self.parse_duration(player.current.length)
                    if not player.current.is_stream
                    else "N/A",
                )
            )
            embed.set_author(
                icon_url=ctx.author.avatar.url, name=self.t("embed", "title")
            )
            self.bot.create_task(ctx.send(embed=embed))
            return

        embeds = []
        j = 0
        embed = None
        for i, track in enumerate(player.queue):
            if j == 0:  # reset embed
                embed = discord.Embed(
                    description=self.t(
                        "embed",
                        "description",
                        track=player.current.title,
                        user=player.ctx.author,
                        current_time=self.parse_duration(player.position),
                        total_time=self.parse_duration(player.current.length)
                        if not player.current.is_stream
                        else "N/A",
                    )
                )
                embed.set_author(
                    icon_url=ctx.author.avatar.url, name=self.t("embed", "title")
                )

            if track.is_stream:
                length_and_estimated = (
                    f"N/A / Est. {self._estimate_time_until(track, player)}"
                )
            else:
                length_and_estimated = f"{self.parse_duration(track.length)} / Est. {self._estimate_time_until(track, player)}"

            embed.add_field(name=f"{i+1}. {track.title}", value=length_and_estimated)

            if j >= 8:
                embeds.append(embed)
                j = 0
                continue

            if i == len(player.queue) - 1:
                embeds.append(embed)
            j += 1

        await Paginator.Simple(ephemeral=True).start(ctx, pages=embeds)

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
            player.skip(force=True), self.send_reaction(ctx, "\u23ed\ufe0f")
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
    async def stop_logic(player: wavelink.Player) -> None:
        player.queue.clear()
        player.autoplay = wavelink.AutoPlayMode.disabled
        player.auto_queue.clear()
        await player.stop()

    @commands.hybrid_command(aliases=["para"])
    async def stop(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return

        await asyncio.gather(
            self.stop_logic(player), self.send_reaction(ctx, "\u23f9\ufe0f")
        )

    @commands.hybrid_command(aliases=["sai", "sair"])
    async def leave(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return

        await asyncio.gather(
            self.send_reaction(ctx, "\u23f9\ufe0f"), ctx.voice_client.disconnect()
        )

    @commands.hybrid_command(aliases=["entra"])
    async def join(self, ctx: commands.Context) -> None:
        if not await self.ensure_voice(ctx):
            return
        if ctx.author.voice.channel == ctx.voice_client.channel:
            await ctx.send(self.t("err", "already_connected"))
            return

    @commands.hybrid_command(aliases=["embaralhar", "misturar"])
    async def shuffle(self, ctx: commands.Context) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.reply(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.reply(self.t("not_playing"))
            return
        if not player.queue:
            await ctx.reply(self.t("cmd", "queue_empty"))
            return

        player.queue.shuffle()
        await ctx.send(self.t("cmd", "output"))

    @staticmethod
    def nice_filter_name(filter_name: str) -> str:
        if filter_name == "reverb":
            filter_name = "slowed + reverb"
        return filter_name.replace("_", " ").title()

    async def filter_show_logic(self, ctx: commands.Context) -> None:
        # list all filters
        if ctx.invoked_subcommand is None:
            filter_cmd_list = [
                cmd.name for cmd in self.bot.get_command("filter").commands
            ]  # type: ignore
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
        voice = "Joana" if lang == "pt" else "Olivia"
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

    @commands.hybrid_command(help="+10 -10")
    async def seek(self, ctx: commands.Context, secs: str) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if not player.playing:
            await ctx.send(self.t("not_playing"))
            return

        if secs.startswith("+"):
            seek_to = (int(secs[1:]) * 1000) + player.position
        elif secs.startswith("-"):
            seek_to = player.position - (int(secs[1:]) * 1000)
        else:
            seek_to = int(secs) * 1000

        self.bot.create_task(player.seek(seek_to))
        self.bot.create_task(
            ctx.send(
                self.t(
                    "cmd",
                    "output",
                    position=self.parse_duration(player.position),
                    time=self.parse_duration(seek_to),
                )
            )
        )

    @commands.hybrid_command(aliases=["vol", "v"])
    async def volume(self, ctx: commands.Context, volume: Optional[int] = None) -> None:
        player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            await ctx.send(self.t("not_in_voice"))
            return
        if volume:
            if volume < 0 or volume > 1000:
                await ctx.send(self.t("err", "volume_out_of_range"))
                return

            await asyncio.gather(
                player.set_volume(volume),
                ctx.send(self.t("cmd", "output", volume=volume)),
            )
        else:
            await ctx.send(self.t("cmd", "volume", volume=player.volume))

    @staticmethod
    def get_expected_file_size(duration: int) -> int:
        return duration * ((320 * 1000) // 8)

    @staticmethod
    def get_tmp_size() -> int:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk("/tmp"):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size

    @commands.hybrid_command(aliases=["transferir", "dl"])
    async def download(self, ctx: commands.Context, *, query: str) -> None:
        query = query.strip("<>")

        # download with info
        msg: discord.Message
        async with ctx.typing():
            info, msg = await asyncio.gather(
                self.bot.loop.run_in_executor(
                    None, self.ytdlp_download.extract_info, query, False
                ),
                ctx.send(self.t("cmd", "checking")),
            )

            # check for query
            if "entries" in info:
                info = info["entries"][0]

            # check if the file is bigger than 25MB
            # TODO: This can mostly be removed, we can just check if the duration is bigger than 660 seconds (11 minutes aprox. 25MB)
            if self.get_expected_file_size(info["duration"]) > 25 * 1024 * 1024:
                self.bot.create_task(msg.edit(content=self.t("err", "file_too_big")))
                return

            # check if the /tmp folder is bigger than 1GB, if it is, wait 5 seconds and try again
            if self.get_tmp_size() > 1024 * 1024 * 1024:
                total_time = 0
                await msg.edit(
                    content=self.t("cmd", "too_many_downloads", time=total_time)
                )
                while self.get_tmp_size() > 1024 * 1024 * 1024:
                    await asyncio.sleep(5)
                    await msg.edit(
                        content=self.t("cmd", "too_many_downloads", time=total_time)
                    )
                    total_time += 5
                    if total_time > 60:
                        self.bot.create_task(
                            msg.edit(content=self.t("err", "too_many_downloads"))
                        )
                        return

            # download the file
            await asyncio.gather(
                self.bot.loop.run_in_executor(
                    None, self.ytdlp_download.download, [query]
                ),
                msg.edit(content=self.t("cmd", "downloading")),
            )

            self.bot.create_task(msg.edit(content=self.t("cmd", "sending")))

            # get the file name
            file_name = self.ytdlp_download.prepare_filename(info)

            # change whatever extension is to .mp3
            last_dot_index = file_name.rfind(".")
            file_extension = file_name[last_dot_index:]
            file_name = file_name.replace(file_extension, ".mp3")

            # send the file
            self.bot.create_task(ctx.send(file=discord.File(file_name)))

            self.bot.create_task(
                msg.edit(
                    content=self.t(
                        "cmd", "finished", title=info["title"], author=info["uploader"]
                    )
                )
            )
            self.bot.create_task(aiofiles.os.remove(file_name))

    # TODO: actually implement this
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
        parsed_position = self.parse_duration(player.position)
        total = track.length
        parsed_length = self.parse_duration(total)
        progress_bar = self.make_progress_bar(round(player.position / 1000), total)

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
        embed.add_field(name=self.t("embed", "subs"), value=f':envelope: {"SUBS"}')
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
