import wavelink
from discord.ext import commands
import psutil

from typing import Union

class Music(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

        self.bot.loop.create_task(self.connect_nodes())
        self.node = None
        self.queue = wavelink.Queue
        

    def check_lavalink(self) -> bool:
        """Check if Lavalink is running."""
        for p in psutil.process_iter():
            if p.name() == "java":
                if "Lavalink.jar" in p.cmdline()[2]:
                    return True
        
        return False
    
    async def connect_nodes(self) -> None:
        """Connect to Lavalink nodes."""
        await self.bot.wait_until_ready()
        if not self.check_lavalink():
            try:
                raise wavelink.LavalinkException("Lavalink is not running! Please start it before starting the bot.")
            finally:
                exit(1)

        self.node = await wavelink.NodePool.create_node(
            bot=self.bot,
            host="0.0.0.0",
            port=2333,
            password=self.bot.lavalink_password
        )
        
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        """Log when a node is ready."""
        self.log(20, f"Node {node} is ready.")




    @commands.hybrid_command(name="play")
    async def play_command(self, ctx, *, query: str)-> None:

        if not ctx.voice_client:
            await ctx.send(self.t("play", "connect", channel=ctx.author.voice.channel.mention))
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client
        
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)

        if not vc.is_playing():
            await vc.play(track)
        else:
            await vc.queue.put(track)
            await ctx.send(self.t("play", "queued", track=track.title))









        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        await self.node.disconnect()
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Music")