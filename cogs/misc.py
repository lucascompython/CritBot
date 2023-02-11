import traceback
from datetime import datetime
from typing import Optional

import discord
import orjson
from aiofiles import open as async_open
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.ext import commands


async def save_bug_report(user_id: int, guild: discord.Guild, title: str, message: str, timestamp: datetime):
    data = None

    async with async_open("./logs/bug_reports.json", "r") as f:
        try:
            data = orjson.loads(await f.read())
        except orjson.JSONDecodeError:
            data = {}


    data[timestamp.isoformat()] = {
        "user_id": user_id,
        "user_name": discord.utils.get(guild.members, id=user_id).name,
        "guild_name": guild.name,
        "guild_id": guild.id,
        "title": title,
        "message": message
    }

    async with async_open("./logs/bug_reports.json", "wb") as f:
        await f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))


class Misc(commands.Cog):



    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        I18N = [self.bot.i18n]

        self.log = self.bot.logger.log

        self.show_info_cmd = app_commands.ContextMenu(name="show_info", callback=self.show_info_interaction, extras={"cog_name": "misc"})
        self.bug_report_cmd= app_commands.Command(name="bug_report", description="command_description" , callback=self.bug_report, extras={"cog_name": "misc", "command_name": "bug_report"})
        self.bot.tree.add_command(self.show_info_cmd)
        self.bot.tree.add_command(self.bug_report_cmd)

        #TODO fix this, this only works if the testing_guild is already in the database
        class BugReport(discord.ui.Modal, title="Bugs" if not I18N[0].guild_id else self.t("modal", "modal_title", mcommand_name="bug_report", mcog_name="misc")):


            def __init__(self, *args, guild_id: int, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                I18N[0].guild_id = guild_id

            

            _title = discord.ui.TextInput(label=I18N[0].t("modal", "title", mcommand_name="bug_report", mcog_name="misc"), placeholder=I18N[0].t("modal", "title_placeholder", mcommand_name="bug_report", mcog_name="misc"))
            description = discord.ui.TextInput(label=I18N[0].t("modal", "description", mcommand_name="bug_report", mcog_name="misc"), placeholder=I18N[0].t("modal", "description_placeholder", mcommand_name="bug_report", mcog_name="misc"), style=discord.TextStyle.long, max_length=300)
                

            async def on_submit(self, interaction: discord.Interaction):
                await save_bug_report(interaction.user.id, interaction.guild, self._title.value, self.description.value, datetime.now())
                await interaction.response.send_message(I18N[0].t("modal", "thank_you", mcommand_name="bug_report", mcog_name="misc"), ephemeral=True)

            async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
                await interaction.response.send_message(I18N[0].t("modal", "oops", mcommand_name="bug_report", mcog_name="misc"), ephemeral=True)

                traceback.print_exception(type(error), error, error.__traceback__)

        self.bug_report_modal = BugReport











    def show_info_builder(self, member: discord.Member) -> discord.Embed:

        embed = discord.Embed(
            title=self.t("embed", "title"),
            description=member.mention,
            color=member.color,
        )
        embed.set_author(name=member, icon_url=member.avatar.url)
        embed.set_footer(text="ID: " + str(member.id))
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name=self.t("embed", "joined_at"), value=discord.utils.format_dt(member.joined_at))
        position = sorted(member.guild.members, key= lambda m: m.joined_at).index(member) + 1
        embed.add_field(name=self.t("embed", "entry_position"), value=position)
        embed.add_field(name=self.t("embed", "created_at"), value=discord.utils.format_dt(member.created_at))
        embed.add_field(name=self.t("embed", "activity"), value=", ".join([activity.name for activity in member.activities]) if member.activities else "N/A")
        embed.add_field(name=self.t("embed", "status"), value=str(member.status).capitalize())
        embed.add_field(name=self.t("embed", "is_on_mobile"), value=self.t("embed", "true") if member.is_on_mobile() else self.t("embed", "false"))
        embed.add_field(name=self.t("embed", "premium"), value=discord.utils.format_dt(member.premium_since) if member.premium_since else self.t("embed", "false"))
        embed.add_field(name=self.t("embed", "top_role"), value=member.top_role.mention)
        embed.add_field(name="Bot", value=self.t("embed", "true") if member.bot else self.t("embed", "false"))
        embed.timestamp = datetime.now()

        return embed






    async def show_info_interaction(self, interaction: discord.Interaction, member: discord.Member):
        member = interaction.guild.get_member(member.id)
        self.bot.i18n.command_name = "show_info"
        embed = self.show_info_builder(member)
        await interaction.response.send_message(embed=embed)


    @commands.hybrid_command(aliases=["info", "whois"])
    async def userinfo(self, ctx, member: Optional[discord.Member]):
        member = member or ctx.author
        self.bot.i18n.command_name = "show_info"
        embed = self.show_info_builder(member)
        await ctx.send(embed=embed)



    @commands.hybrid_command(aliases=["latency", "latencia"])
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000, 3)
        await ctx.send(self.t("cmd", "output", latency=latency))

    @commands.hybrid_command(aliases=["convite"])
    async def invite(self, ctx):
        await ctx.send(self.t("cmd", "output", invite=self.bot.invite_link))
    
    @commands.hybrid_command(aliases=["repository", "repo", "repositorio", "github", "git"])
    async def source_code(self, ctx):
        await ctx.send(self.t("cmd", "output", source_link=self.bot.source_link))


    @commands.hybrid_command(name="bot_info", aliases=["botinfo", "bot"])
    async def _bot_info(self, ctx):
        embed = discord.Embed(
            title=self.t("embed", "title"),
            color=discord.Color.blurple()
        )
        embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar.url)
        embed.set_footer(text="ID: " + str(self.bot.user.id))

        embed.add_field(name=self.t("embed", "guilds"), value=len(self.bot.guilds))
        embed.add_field(name=self.t("embed", "users"), value=len(self.bot.users))
        embed.add_field(name=self.t("embed", "latency"), value=str(round(self.bot.latency * 1000, 3)) + "ms")
        embed.add_field(name=self.t("embed", "commands"), value=len(self.bot.commands))
        embed.add_field(name=self.t("embed", "repository"), value=self.t("embed", "repository_link", repository_link=self.bot.source_link))
        embed.add_field(name=self.t("embed", "invite"), value=self.t("embed", "invite_link", invite_link=self.bot.invite_link))
        embed.add_field(name=self.t("embed", "developer"), value=self.bot.get_user(self.bot.owner_id))
        embed.add_field(name=self.t("embed", "uptime"), value=self.bot.uptime)
        embed.timestamp = datetime.now()

        await ctx.send(embed=embed)


    async def bug_report(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.bug_report_modal(guild_id=interaction.guild_id))


    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))



async def setup(bot) -> None:
    await bot.add_cog(Misc(bot))

async def teardown(bot) -> None:
    await bot.remove_cog("Misc")
