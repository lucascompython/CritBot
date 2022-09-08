from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.logger.log(20, f"Joined {guild.name} ({guild.id})")
        self.bot.update_prefixes(guild.id, self.bot.default_prefix)
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.logger.log(20, f"Left {guild.name} ({guild.id})")
        self.bot.delete_prefix(guild.id)

        
    async def cog_load(self) -> None:
        self.bot.logger.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        self.bot.logger.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Events(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Events")