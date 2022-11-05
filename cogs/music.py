import asyncio
import psutil
import discord
import wavelink
from yt_dlp import YoutubeDL # for extra info TODO add shorts, stories and tiktok 
from discord.ext import tasks
from discord.ext import commands



import sys
import asyncio
import datetime
import functools





class AudioSourceTracked(discord.AudioSource):
    def __init__(self, source):
        self._source = source
        self.count_20ms = 0

    def read(self) -> bytes:
        data = self._source.read()
        if data:
            self.count_20ms += 1
        return data

    @property
    def progress(self) -> float:
        return self.count_20ms * 0.02 # count_20ms * 20ms


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

        bot.loop.create_task(self.connect_nodes())
        self.node = None
        self.loop = asyncio.get_event_loop()
        self.ytdl_options = {
            "extractaudio": False,
            "skip_download": True,
            "quiet": True
        }
        self.ytdl = YoutubeDL(self.ytdl_options)
        

    def check_lavalink(self) -> bool:
        """Check if Lavalink is running."""
        for p in psutil.process_iter():
            if p.name() == "java":
                if any("Lavalink" in string for string in p.cmdline()):
                    return True
        
        return False
    
    async def connect_nodes(self):
        """Connect to Lavalink nodes."""
        await self.bot.wait_until_ready()
        if not self.check_lavalink():
            sys.stderr.write("Lavalink is not running! Please start it before starting the bot.\n")
            exit(1)

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
    def parse_duration(duration: int) -> str:
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


    async def get_dislikes(self, track_id: str) -> int | None:
        """Get the dislikes of a video.

        Args:
            track_id (str): The track id.

        Returns:
            int: The dislikes.
        """
        async with self.bot.web_client.get(f"https://returnyoutubedislikeapi.com/votes?videoId={track_id}") as resp:
            data = await resp.json()
            return data["dislikes"]


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
        if dislikes: dislikes = self.human_format(dislikes)
        
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


        return embed





    @commands.hybrid_command(aliases=["p"])
    async def play(self, ctx, *, query: str) -> None:

        if not ctx.voice_client:
            await ctx.send(self.t("cmd", "connect", channel=ctx.author.voice.channel.mention))
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client
        
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
        track.info["context"] = ctx

        if not vc.is_playing():
            await ctx.send(embed=await self.embed_generator(track, ctx.author))
            await vc.play(track)
        else:
            vc.queue.put(track)
            await ctx.send(self.t("cmd", "queued", track=track.title))
    


    @commands.hybrid_command(aliases=["s"])
    async def skip(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client

        if not vc:
            return await ctx.send(self.t("err", "not_connected"))

        if not vc.is_playing():
            return await ctx.send(self.t("err", "not_playing"))

        if vc.queue.count < 1:
            return await ctx.send(self.t("err", "queue_empty"))
        
        await vc.stop()
        await ctx.message.add_reaction("⏭️")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason: str):
        """Play the next song in the queue."""
        if player.queue.is_empty:
            return
        
        track = await player.queue.get_wait()

        ctx = track.info["context"]
        requester = ctx.author
        embed = await self.embed_generator(track, requester)
        await ctx.send(embed=embed)

        
        await player.play(track)







    @commands.hybrid_command(aliases=["q"])
    async def queue(self, ctx) -> None:
        vc: wavelink.Player = ctx.voice_client
        if not vc:
            return await ctx.send(self.t("err", "not_connected"))
        if not vc.is_playing():
            return await ctx.send(self.t("err", "empty"))
            
        time = AudioSourceTracked(vc.track).progress
        print(time)
        embed = discord.Embed(title="queue", description=self.t("embed", "title", track=vc.track.title, user=vc.info["context"].author, current_time=time, total_time=self.parse_duration(vc.track.duration)))
        for i, track in enumerate(vc.queue._queue):
            embed.add_field(name=f"{i+1}. {track.title}", value=self.parse_duration(track.duration), inline=False)
        await ctx.send(embed=embed)













        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        await self.node.disconnect()
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Music")