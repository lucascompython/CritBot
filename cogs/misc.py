from discord.ext import commands




class Misc(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot


    @commands.hybrid_command()
    async def ping(self, ctx):
        """Ping do bot."""
        await ctx.send(f"O meu ping é {round(self.bot.latency * 1000, 3)}ms.")

    @commands.hybrid_command()
    async def invite(self, ctx):
        """Get the bot's invite link."""
        await ctx.reply("My invite link is: https://discord.com/api/oauth2/authorize?client_id=832679098740506644&permissions=8&scope=bot")


    async def cog_load(self) -> None:
        self.bot.logger.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        self.bot.logger.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))



async def setup(bot) -> None:
    await bot.add_cog(Misc(bot))

async def teardown(bot) -> None:
    await bot.remove_cog("Misc")
