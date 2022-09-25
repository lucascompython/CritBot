from discord.ext import commands



class Misc(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log



    @commands.hybrid_command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000, 3)
        await ctx.send(self.t("cmd", "output", latency=latency))

    @commands.hybrid_command()
    async def invite(self, ctx):
        await ctx.send(self.t("cmd", "output", invite=self.bot.invite_link))
    
    @commands.hybrid_command()
    async def source_code(self, ctx):
        await ctx.send(self.t("cmd", "output", source_link=self.bot.source_link))






    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))



async def setup(bot) -> None:
    await bot.add_cog(Misc(bot))

async def teardown(bot) -> None:
    await bot.remove_cog("Misc")
