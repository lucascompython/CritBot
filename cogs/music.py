import discord
import wavelink
from yt_dlp import YoutubeDL # for extra info TODO add shorts, stories and tiktok 
from discord.ext import commands


import re
import asyncio
import datetime
import functools
from typing import Union, Optional
from aiohttp import ContentTypeError

from Utils import Paginator

#TODO optimize errors for example: the error not connected can be in a global error handler
#TODO see if it is worth making a decorator for the commands that need the voice player and have the same checks for example: if not vc.is_playing: await ctx.send(self.t("not_playing"))

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

        self.bot.loop.create_task(self.connect_nodes())
        self.node = None
        self.loop = asyncio.get_event_loop()
        self.ytdl_options = {
            "extractaudio": False,
            "skip_download": True,
            "quiet": True
        }
        self.ytdl = YoutubeDL(self.ytdl_options)
        

    
    async def connect_nodes(self):
        """Connect to Lavalink nodes."""
        await self.bot.wait_until_ready()

        self.node = await wavelink.NodePool.create_node(
            bot=self.bot,
            host=self.bot.lavalink["ip"],
            port=self.bot.lavalink["port"],
            password=self.bot.lavalink["password"]
        )
        
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Log when a node is ready."""
        self.log(20, f"Node <{node.identifier}> is ready.")


    @staticmethod
    def parse_duration(duration: float | int) -> str:
        value = str(datetime.timedelta(seconds = duration))
        return value
    
    @staticmethod
    def human_format(num: int) -> str:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


    async def get_dislikes(self, track_id: str) -> int | str | None:
        """Get the dislikes of a video.

        Args:
            track_id (str): The track id.

        Returns:
            int: The dislikes.
        """
        async with self.bot.web_client.get(f"https://returnyoutubedislikeapi.com/votes?videoId={track_id}") as resp:
            try:
                data = await resp.json()
                return data["dislikes"]
            except ContentTypeError:
                return "N/A"



    async def embed_generator(self, track: wavelink.YouTubeTrack, author: discord.Member) -> discord.Embed:
        """Helper function that generates a embed that is sent when a music is played.

        Args:
            track (wavelink.YouTubeTrack): The track in question.
            author (discord.Member): The member that requested the track.

        Returns:
            discord.Embed: The embed.
        """
        #TODO check if likes and shit can be 0
        partial = functools.partial(self.ytdl.extract_info, track.identifier, download=False, process=False)
        track_info = await self.loop.run_in_executor(None, partial)
        views = track_info.get("view_count")
        likes = track_info.get("like_count")
        date = track_info.get("upload_date")
        thumbnail = track_info.get("thumbnail")
        subs = track_info.get("channel_follower_count", 0)
        uploader_url = track_info.get("uploader_url")
        upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        dislikes = await self.get_dislikes(track.identifier)
        if subs: subs = self.human_format(subs)
        if views: views = self.human_format(views)
        if likes: likes = self.human_format(likes)
        if type(dislikes) != str: dislikes = self.human_format(dislikes)
        
        #TODO estimated time until play

        self.bot.i18n.command_name = "play"
        time = self.parse_duration(track.duration)
        embed = discord.Embed(title=self.t("embed", "title", source=track.info["sourceName"].capitalize()), description=f"```{track.title}```")
        embed.set_thumbnail(url=thumbnail)

        embed.set_author(name=self.t("embed", "author", user=author.name), icon_url=author.avatar.url)
        embed.set_footer(text=self.t("embed", "footer", upload_date=upload_date))

        embed.add_field(name=self.t("embed", "duration"), value=time)
        embed.add_field(name=self.t("embed", "uploader"), value=f"[{track.author}]({uploader_url})")
        embed.add_field(name="URL", value=self.t("embed", "click", url=track.uri))
        embed.add_field(name=self.t("embed", "views"), value=views)
        embed.add_field(name=self.t("embed", "likes_dislikes"), value=f"{likes} / {dislikes}")
        embed.add_field(name=self.t("embed", "subs"), value=subs)
        embed.timestamp = datetime.datetime.now()


        return embed



    async def _add_to_queue(self, tracks: wavelink.YouTubeTrack | wavelink.YouTubePlaylist, player: wavelink.Player, ctx: commands.Context, playlist: Optional[wavelink.YouTubePlaylist] = None) -> None:
        self.bot.i18n.command_name = "play"
        if playlist:
            for track in tracks:
                track.info["context"] = ctx
                await player.queue.put_wait(track)
                #TODO get the playlist author
            return await ctx.send(self.t("cmd", "queued_playlist", length=len(tracks), playlist=playlist.name))





    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        #TODO see wavelink.SearchableTrack.convert


        vc: wavelink.Player = await self._join(ctx, _play="comesfromplaycommand")

        query.strip("<>")

        link_regex = "((http(s)*:[/][/]|www.)([a-z]|[A-Z]|[0-9]|[/.]|[~])*)"
        pattern = re.compile(link_regex)
        match_url = re.match(pattern, query)
        query = query.replace("/", "%2F") if match_url is None else query

        playlist_regex = r"watch\?v=.+&(list=[^&]+)"
        matches = re.search(playlist_regex, query)

        groups = matches.groups() if matches is not None else []
        is_playlist = len(groups) > 0 or "playlist" in query

        if not is_playlist:
            #TODO check this, seach function apparently can return a playlist
            track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
            #track.info["context"] = ctx
            #track.info["loop"] = False
        else:
            playlist = await wavelink.YouTubePlaylist.search(query=query)
            tracks = playlist.tracks

        if not vc.is_playing():
            if is_playlist:
                track = tracks[0]
            track.info["context"] = ctx
            track.info["loop"] = False

            await ctx.send(embed=await self.embed_generator(track, ctx.author))
            await vc.queue.put_wait(track)
            track = await vc.queue.get_wait()
            await vc.play(track)
            if is_playlist:
                await self._add_to_queue(tracks[1:], vc, ctx, playlist)
        else:
            if not is_playlist:
                track.info["context"] = ctx
                track.info["loop"] = False
                await vc.queue.put_wait(track)
                return await ctx.send(self.t("cmd", "queued", track=track.title, author=track.author))
            
            await self._add_to_queue(tracks, vc, ctx, playlist)
    


    @commands.hybrid_command(aliases=["s"])
    async def skip(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send(self.t("not_connected"))

        if not vc.is_playing():
            return await ctx.reply(self.t("not_playing"))

        
        await vc.stop()
        await ctx.message.add_reaction("??????")


    @commands.hybrid_command(aliases=["pausa"])
    async def pause(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send(self.t("not_connected"))
        
        if not vc.is_playing():
            return await ctx.reply(self.t("not_playing"))

        if vc.is_paused():
            return await ctx.reply(self.t("err", "already_paused"))

        await vc.pause()
        await ctx.message.add_reaction("??????")


    @commands.hybrid_command(aliases=["resuma"])
    async def resume(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send(self.t("not_connected"))
        
        if not vc.is_playing():
            return await ctx.reply(self.t("not_playing"))
        
        if not vc.is_paused():
            return await ctx.reply(self.t("err", "not_paused"))

        await vc.resume()
        await ctx.message.add_reaction("??????")


    @commands.hybrid_command(aliases=["vol"])
    async def volume(self, ctx, volume: str | None) -> None:
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send(self.t("not_connected"))
        
        if not vc.is_playing():
            return await ctx.reply(self.t("not_playing"))

        if not volume:
            return await ctx.reply(self.t("cmd", "volume", volume=vc.volume))
        
        if not volume.isdigit():
            return await ctx.reply(self.t("err", "not_int"))

        volume.strip("%")
        volume = int(volume)


        if volume > 100:
            return await ctx.reply(self.t("err", "too_high"))
        
        if volume < 0:
            return await ctx.reply(self.t("err", "too_low"))


        await vc.set_volume(volume)
        await ctx.send(self.t("cmd", "output", volume=volume))


    #TODO add paginator
    @commands.hybrid_command(aliases=["h", "historico", "hist??rico"])
    async def history(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client
        try:
            embed = discord.Embed(description="\n".join([f'[{i+1}]({track.uri}) -- `{track.title}` {self.t("embed", "by")} `{track.info["context"].author}`' for i, track in enumerate(reversed(vc.queue.history))]))
            embed.set_author(name=self.t("embed", "title", user=ctx.author.name), icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        except AttributeError:
            return await ctx.reply(self.t("err", "no_history"))



    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason: str):
        """Play the next song in the queue."""
        if player.queue.history[-1].info["loop"]:
            track.info["loop"] = True
            return await player.play(track)

        if player.queue.is_empty:
            return

        track = await player.queue.get_wait()


        ctx = track.info["context"]
        requester = ctx.author
        embed = await self.embed_generator(track, requester)
        await ctx.send(embed=embed)

        
        await player.play(track)


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):

        #Handle bot being kicked from the channel
        if member.id == self.bot.user.id and after.channel is None:
            player: wavelink.Player = before.channel.guild.voice_client
            return await player.disconnect() if player else None


        #if the bot is left alone in a channel disconnect
        if not member.bot and after.channel is None:
            player: wavelink.Player = before.channel.guild.voice_client
            if not [m for m in before.channel.members if not m.bot]:
                return await player.disconnect()
        
        

        #TODO fix this
        #if there are people on the channel but the bot is not playing wait 3 min and then disconnect
        #elif member.id != self.bot.user.id:
            #return
        #elif before.channel is None:
            #voice: wavelink.Player = after.channel.guild.voice_client
            #time = 0
            #while True:
                #await asyncio.sleep(1)
                #time += 1
                ##TODO fix when paused it leaves 
                #if voice.is_playing() and not voice.is_paused():
                    #time = 0
                #if time == 180:
                    #await voice.disconnect()
                #if not voice.is_connected():
                    #break


    @commands.hybrid_command(aliases=["sai"])
    async def leave(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send(self.t("not_connected"))

        await vc.disconnect()
        await ctx.message.add_reaction("????")
    
    @commands.hybrid_command(name="join", aliases=["entra"])
    async def _join(self, ctx, *, channel: discord.VoiceChannel = None, _play: str = None) -> wavelink.Player:
        if not ctx.author.voice:
            return await ctx.reply(self.t("err", "not_in_voice", mcommnand_name="join"))
        if not ctx.voice_client and not channel:
            channel = ctx.author.voice.channel
            await ctx.send(self.t("cmd", "connect", channel=ctx.author.voice.channel.mention, mcommand_name="join"))
            return await channel.connect(cls=wavelink.Player)
            
        else:
            vc: wavelink.Player = ctx.voice_client
            if not _play == "comesfromplaycommand":
                await ctx.send(self.t("err", "already_connected", mcommand_name="join"))
            return vc
        

    def _estimate_time_until(self, track: wavelink.abc.Playable, player: wavelink.Player) -> str:
        """Estimate the time until the given position."""
        index = player.queue._queue.index(track)
        queue_until_track = list(player.queue._queue)[:index]
        estimated_time = sum(track.length for track in queue_until_track)
        for i in queue_until_track:
            estimated_time += i.length

        if player.is_playing:
            estimated_time += player.track.length - player.position
        
        return self.parse_duration(round(estimated_time))


    @commands.hybrid_command(aliases=["q"])
    async def queue(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client
        if not vc:
            return await ctx.send(self.t("not_connected"))
        if not vc.is_playing():
            return await ctx.send(self.t("queue_empty"))
            
        progress = round(vc.position)
        # if only 1 track is in the queue (the one that is playing)
        if len(vc.queue._queue) == 0:
            embed = discord.Embed(description=self.t("embed", "description", track=vc.track.title, user=vc.track.info["context"].author, current_time=self.parse_duration(progress), total_time=self.parse_duration(vc.track.duration)))
            embed.set_author(icon_url=ctx.author.avatar.url, name=self.t("embed", "title"))
            return await ctx.send(embed=embed)

        # paginator
        embeds = []
        j = 0
        embed = None
        for i, track in enumerate(vc.queue._queue):
            if j ==  0: # reset embed
                embed = discord.Embed(description=self.t("embed", "description", track=vc.track.title, user=vc.track.info["context"].author, current_time=self.parse_duration(progress), total_time=self.parse_duration(vc.track.duration)))
                embed.set_author(icon_url=ctx.author.avatar.url, name=self.t("embed", "title"))
            if j < 9:
                embed.add_field(name=f"{i+1}. {track.title}", value=f"{self.parse_duration(track.duration)} / Est. {self._estimate_time_until(track, vc)}", inline=False)
            else:
                embed.add_field(name=f"{i+1}. {track.title}", value=f"{self.parse_duration(track.duration)} / Est. {self._estimate_time_until(track, vc)}", inline=False)
                embeds.append(embed)
                j = 0
                continue
            if i == len(vc.queue._queue) -1:
                embeds.append(embed)
            j += 1
        
        await Paginator.Simple(ephemeral=True).start(ctx, pages=embeds)



    @commands.hybrid_command()
    async def stop(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client
        if not vc:
            return await ctx.send(self.t("not_connected"))
        if not vc.is_playing():
            return await ctx.send(self.t("queue_empty"))
        vc.queue.clear()
        await vc.stop()
        await ctx.message.add_reaction("??????")


    @commands.hybrid_command(name="loop", aliases=["repeat"])
    async def _loop(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client
        if not vc:
            return await ctx.send(self.t("not_connected"))
        if not vc.is_playing():
            return await ctx.send(self.t("queue_empty"))
        track = vc.track

        if not track.info["loop"]:
            track.info["loop"] = True
            await ctx.message.add_reaction("????")
        else:
            vc.queue.history[-1].info["loop"] = False
            await ctx.message.add_reaction("????")



    #TODO Mess with this
    #@commands.hybrid_command()
    #async def filter(self, ctx, filter: str) -> None:
        #vc: wavelink.Player = ctx.voice_client
        #if filter in ["clear", "off", "reset"]:
            #await vc.set_filter(wavelink.Filter())
        ##if not vc:
            ##return await ctx.send(self.t("err", "not_connected"))
        ##if not vc.is_playing():
            ##return await ctx.send(self.t("err", "empty"))
        #await vc.set_filter(wavelink.Filter(equalizer=wavelink.Equalizer.boost), seek=True)
        ##await ctx.send(self.t("cmd", "filter", filter=filter.name))


    #TODO make this wiht buttons, and add a better portuguese name to this
    @commands.hybrid_command()
    async def seek(self, ctx, time: int) -> None:
        vc: wavelink.Player = ctx.voice_client
        time = time * 1000
        await vc.seek(time)
        position = self.parse_duration(round(vc.position))
        time_so_seek_to = self.parse_duration(time / 1000)
        await ctx.send(self.t("cmd", "output", position=position, time=time_so_seek_to))





    #TODO make a panel with buttons 


        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        await self.node.disconnect()
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Music")