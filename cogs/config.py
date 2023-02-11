from discord.ext import commands


class Config(commands.Cog):
    """Manage the bot's configuration."""
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        

    @commands.hybrid_command(aliases=["mudar_prefixo"])
    async def change_prefix(self, ctx, prefix) -> None:
        try:
            await self.bot.update_prefixes(ctx.guild.id, prefix)
            await ctx.send(self.t("cmd", "output", prefix=prefix))
        except ValueError:
            await ctx.send(self.t("err", "same_prefix", prefix=prefix))

    @commands.hybrid_command(aliases=["change_lang", "mudar_idioma", "mudar_linguagem", "mudar_lingua", "mudar_língua"])
    async def change_language(self, ctx, lang) -> None:
        """Change the bot language."""
        if self.bot.i18n.check_lang(lang):
            try:
                await self.bot.i18n.update_langs(ctx.guild.id, lang)
                await ctx.send(self.t("cmd", "output", lang=lang))
            except ValueError:
                await ctx.send(self.t("err", "same_language", lang=lang))
        else:
            await ctx.send(self.t("err", "invalid_language", lang=lang, langs=", ".join(self.bot.i18n.accepted_langs)))


    
        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Config(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Config")