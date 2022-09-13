from typing import Literal
import discord
from discord.ext import commands
from discord import app_commands



class Interactions(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t


        self.ctx_menu = app_commands.ContextMenu(name="Reportar a mensagem", callback=self.report_message)
        self.bot.tree.add_command(self.ctx_menu)
        self.ctx_menu = app_commands.ContextMenu(name="Mostrar info", callback=self.show_join_date)
        self.bot.tree.add_command(self.ctx_menu)

    @app_commands.command()
    async def slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("OLa")




    async def show_join_date(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f'{member} entrou em {discord.utils.format_dt(member.joined_at)}')

    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        ctx = await self.bot.get_context(interaction)
        await interaction.response.send_message(
            self.t("cmd", "report_message", ctx=ctx, author=message.author.mention)
        ) 
    
        guild = self.bot.get_guild(404691077216600067)
        log_channel = guild.get_channel(810164720832348221) 
        
        embed = discord.Embed(title=self.t("cmd", "embed_title"))
        if message.content:
            embed.description = message.content
    
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.timestamp = message.created_at
    
        url_view = discord.ui.View()
        url_view.add_item(discord.ui.Button(label=self.t("cmd", "button_goto_msg", ctx=ctx), style=discord.ButtonStyle.url, url=message.jump_url))
    
        await log_channel.send(embed=embed, view=url_view)


    @app_commands.command()
    async def shop(self, interaction: discord.Interaction, action: Literal["Comprar", "Vender"], item: str) -> None:
        await interaction.response.send_message(f"Ação: {action}\nItem: {item}")



    async def cog_load(self) -> None:
        self.bot.logger.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        self.bot.logger.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))

async def setup(bot):
    await bot.add_cog(Interactions(bot))

async def teardown(bot):
    await bot.remove_cog("Interactions")

