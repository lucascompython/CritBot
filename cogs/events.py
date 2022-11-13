from discord.ext import commands

import traceback

class Events(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.bot.i18n.command_name = "on_command_error"
        self.bot.i18n.cog_name = "events"
        self.bot.i18n.guild_id = ctx.guild.id


        #TODO add more errors like when the arguments are of the wrong type
        if isinstance(error, commands.NotOwner):
            await ctx.reply(self.t("err", "not_owner"))
        else:
            await ctx.reply(self.t("err", "unknown"))
            self.log(40, error)
            traceback.print_exception(type(error), error, error.__traceback__)



        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Events(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Events")