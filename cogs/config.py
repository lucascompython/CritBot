from discord.ext import commands
from discord import app_commands

class Config(commands.Cog):
    """Manage the bot's configuration."""
    def __init__(self, bot) -> None:
        self.bot = bot
        
    @commands.hybrid_command()
    async def change_prefix(self, ctx, prefix):
        """Change the bot prefix."""
        self.bot.update_prefixes(ctx.guild.id, prefix)
        await ctx.send(f"Prefix changed to **{prefix}**")

        
    async def cog_load(self) -> None:
        self.bot.logger.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        self.bot.logger.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Config(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Config")