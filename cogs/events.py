from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.log = self.bot.logger.log
        

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.update_prefixes(guild.id, self.bot.default_prefix)
        await self.bot.i18n.update_langs(guild.id, self.bot.default_language)
        self.log(20, f"Joined {guild.name} ({guild.id})")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.delete_prefix(guild.id)
        await self.bot.i18n.delete_lang(guild.id)
        self.log(20, f"Left {guild.name} ({guild.id})")

    #@commands.Cog.listener()
    #async def on_command_error(self, ctx, error):
        #print("morre")
        #await self.bot.set_guild_and_cog_and_command(ctx, True)
        ##TODO error handling


        
    async def cog_load(self) -> None:
        self.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        self.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Events(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Events")