from discord import Locale
from discord import app_commands
from discord.app_commands import TranslationContextLocation

from typing import Optional


from .translations import i18n


class Tree(app_commands.CommandTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    async def interaction_check(self, interaction, /) -> bool:
        if not "hybrid" in str(interaction.command):
            i18n.guild_id = interaction.guild_id
            i18n.cog_name = interaction.command.extras["cog_name"]
            i18n.command_name = interaction.command.qualified_name.replace(" ", "_")
        return True



class Translator(app_commands.Translator):
    def __init__(self) -> None:
        super().__init__()


    @staticmethod
    def __get_locale(locale: Locale) -> str | None:
        if locale == Locale.brazil_portuguese or locale == Locale.brazil_portuguese.value:
            return "pt"

        if locale == Locale.american_english or locale == Locale.british_english:
            return "en"

        return None 

    @staticmethod
    def get_translated(mode: str, context: app_commands.TranslationContext, locale: Locale) -> str | None:
        if mode not in ["command_name", "command_description", "group_name", "group_description"]:
            return None
        
        cog = context.data.module.replace("cogs.", "")
        name = context.data.qualified_name.replace(" ", "_")

        match mode:
            case "command_name":
                return i18n.get_command_name(name, cog, locale)
            case "command_description":
                return i18n.get_command_description(name, cog, locale)
            case "group_name":
                return i18n.get_group_name(name, cog, locale)
            case "group_description":
                return i18n.get_group_description(name, cog, locale)
            case _:
                return None

    async def translate(self, string: app_commands.locale_str, locale: Locale, context: app_commands.TranslationContext) -> Optional[str]:
        # translate
        locale = self.__get_locale(locale)


        if not i18n.check_lang(locale):
            return None

        match context.location:
            case TranslationContextLocation.command_name:
                return self.get_translated("command_name", context, locale)
            case TranslationContextLocation.command_description:
                return self.get_translated("command_description", context, locale)
            case TranslationContextLocation.group_name:
                return self.get_translated("group_name", context, locale)
            case TranslationContextLocation.group_description:
                return self.get_translated("group_description", context, locale)

            #TODO add the rest of translations
        

        return None
