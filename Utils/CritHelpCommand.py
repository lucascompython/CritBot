import discord
from discord.ext import commands


class CritHelpCommand(commands.DefaultHelpCommand):
    __slots__ = ("i18n")
    def __init__(self, i18n) -> None:
        super().__init__()
        self.i18n = i18n


    def _get_translated_formatted_commands(self, cog_name: str, commands: list[commands.Command, commands.HybridCommand], guild_id: int) -> list[str]:
        translated_formatted_commands = []

        for command in commands:
            command_name = command.qualified_name.replace(" ", "_")
            translated_command_name = self.i18n.get_app_commands_translation(command_name, cog_name, self.i18n.get_lang(guild_id), "command_name")
            translated_formatted_commands.append(f"`{translated_command_name}`")
        return translated_formatted_commands


    async def send_bot_help(self, mapping):
        channel = self.get_destination()  # this method is inherited from `HelpCommand`, and gets the channel in context
        embed = discord.Embed(color=0xe26b36)
        embed.set_author(icon_url=self.context.author.avatar.url, name=self.i18n.t("title", mcommand_name="help", mcog_name="misc", ctx=self.context))
        # `mapping` is a dict of the bot's cogs, which map to their commands
        guild_id = channel.guild.id
        

        for cog in mapping:
            if not cog: continue
            cog_name: str = cog.__class__.__name__.lower()
            commands = mapping[cog]
            if not commands: continue
            if cog_name == "events": continue
            commands = self._get_translated_formatted_commands(cog_name, commands, guild_id)

            embed.add_field(
                name=f"{cog_name.capitalize()} ({len(commands)})",
                value=", ".join(commands),
                inline=False
            )

        await channel.send(embed=embed)
