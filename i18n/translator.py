from typing import Optional

from discord import Locale, app_commands
from discord.app_commands import TranslationContextLocation


class Translator(app_commands.Translator):
    """
    This class is responsable for translating everything interaction related.
    """

    def __init__(self, i18n) -> None:
        super().__init__()
        self.i18n = i18n

    @staticmethod
    def __get_locale(locale: Locale) -> str | None:
        if (
            locale == Locale.brazil_portuguese
            or locale == Locale.brazil_portuguese.value
        ):
            return "pt"

        if locale == Locale.american_english or locale == Locale.british_english:
            return "en"

        return None

    def get_translated(
        self, mode: str, context: app_commands.TranslationContext, locale: Locale
    ) -> str | None:
        if mode not in [
            "command_name",
            "command_description",
            "group_name",
            "group_description",
        ]:
            return None

        cog = context.data.module.replace("cogs.", "")
        name = context.data.qualified_name.replace(" ", "_")
        return self.i18n.get_app_commands_translation(name, cog, locale, mode)

    async def translate(
        self,
        string: app_commands.locale_str,
        locale: Locale,
        context: app_commands.TranslationContext,
    ) -> Optional[str]:
        locale = self.__get_locale(locale)

        if not self.i18n.check_lang(locale):
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

            # TODO add the rest of translations

        return None
