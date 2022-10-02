from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        



        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Music(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Music")