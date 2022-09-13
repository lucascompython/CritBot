import discord
from discord.ext import commands
from discord import app_commands
import traceback

class Feedback(discord.ui.Modal, title='Feedback'):
    name = discord.ui.TextInput(
        label='Name',
        placeholder='Your name here...',
    )

    feedback = discord.ui.TextInput(
        label='What do you think of this new feature?',
        style=discord.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        traceback.print_tb(error.__traceback__)



class Modals(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        

    @app_commands.command(description="Submit feedback")
    async def feedback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Feedback())







        
    async def cog_load(self) -> None:
        self.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        self.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Modals(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Modals")