from discord import Locale
from discord import app_commands
from discord.app_commands import TranslationContextLocation

from typing import Optional


from .translations import i18n

## Things for the CommandTree
#from discord.app_commands.errors import (
    #MissingApplicationID,
    #CommandSyncFailure,
#)
#from discord.errors import HTTPException
#from discord.abc import Snowflake
#from discord.app_commands.models import AppCommand

#from discord.app_commands.commands import GroupT

######


## Things for the Command
#from discord.app_commands.translator import TranslationContext, TranslationContextLocation
#from discord.ext.commands import Cog
#####



#from typing import Optional, Union, List, Dict, Any, Generic, ParamSpec, TypeVar


#from .translations import I18n



#P = ParamSpec('P')
#T = TypeVar('T')
#GroupT = TypeVar("GroupT", bound="Binding")
#Binding = Union["Group", "Cog"]


#def get_locale_lang(locale: str) -> Union[str, Locale]:
    #"""Helper function to get the proper Locale from a string E.g. "pt" -> Locale.brazil_portuguese

    #Args:
        #locale (str): The string

    #Returns:
        #Union[str, Locale]: Return the proper Locale
    #"""
    #if locale == "pt":
        #return Locale.brazil_portuguese
    
    #if locale == "en":
        #return Locale.american_english

    #return None



#class ContextMenu(app_commands.ContextMenu):
    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)


    
    #async def get_translated_payload(self, translator: app_commands.Translator, lang: Locale) -> Dict[str, Any]:
        #base = self.to_dict()
        #context = TranslationContext(location=TranslationContextLocation.command_name, data=self)
        #if self._locale_name:
            #name_localizations: Dict[str, str] = {}
            #for locale in Locale:
                #if locale == lang:
                    #translation = await translator._checked_translate(self._locale_name, locale, context)
                    #if translation is not None:
                        #name_localizations[locale.value] = translation

            #base['name_localizations'] = name_localizations
        #return base




#class Group(app_commands.Group):
    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)

    #async def get_translated_payload(self, translator: app_commands.Translator, lang: Locale) -> Dict[str, Any]:
        #base = self.to_dict()
        #name_localizations: Dict[str, str] = {}
        #description_localizations: Dict[str, str] = {}

        ## Prevent creating these objects in a heavy loop
        #name_context = TranslationContext(location=TranslationContextLocation.group_name, data=self)
        #description_context = TranslationContext(location=TranslationContextLocation.group_description, data=self)
        #for locale in Locale:
            #if locale == lang:
                #if self._locale_name:
                    #translation = await translator._checked_translate(self._locale_name, locale, name_context)
                    #if translation is not None:
                        #name_localizations[locale.value] = translation

                #if self._locale_description:
                    #translation = await translator._checked_translate(self._locale_description, locale, description_context)
                    #if translation is not None:
                        #description_localizations[locale.value] = translation

        #base['name_localizations'] = name_localizations
        #base['description_localizations'] = description_localizations
        #base['options'] = [await child.get_translated_payload(translator) for child in self._children.values()]
        #return base





#class Command(app_commands.Command, Generic[GroupT, P, T]):
    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)


    #async def get_translated_payload(self, translator: app_commands.Translator, lang: str) -> Dict[str, Any]:
        #base = self.to_dict()
        #name_localizations: Dict[str, str] = {}
        #description_localizations: Dict[str, str] = {}

        ## Prevent creating these objects in a heavy loop
        #name_context = TranslationContext(location=TranslationContextLocation.command_name, data=self)
        #description_context = TranslationContext(location=TranslationContextLocation.command_description, data=self)

        #print("self1")
        #for locale in Locale:
            #print(f"locale: {locale}, locale.value: {locale.value}")
            #if locale.value == lang:
                #if self._locale_name:
                    #translation = await translator._checked_translate(self._locale_name, locale, name_context)
                    #if translation is not None:
                        #name_localizations[locale.value] = translation

                #if self._locale_description:
                    #translation = await translator._checked_translate(self._locale_description, locale, description_context)
                    #if translation is not None:
                        #description_localizations[locale.value] = translation

        #base['name_localizations'] = name_localizations
        #base['description_localizations'] = description_localizations
        #base['options'] = [
            #await param.get_translated_payload(translator, app_commands.Parameter(param, self)) for param in self._params.values()
        #]
        #return base




class Tree(app_commands.CommandTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    async def interaction_check(self, interaction, /) -> bool:
        if not "hybrid" in str(interaction.command):
            i18n.guild_id = interaction.guild_id
            i18n.cog_name = interaction.command.extras["cog_name"]
            i18n.command_name = interaction.command.qualified_name.replace(" ", "_")
        return True


    #def _get_all_commands(
        #self, *, guild: Optional[Snowflake] = None
    #) -> List[Union[Command[Any, ..., Any], Group, ContextMenu]]:
        #if guild is None:
            #base: List[Union[Command[Any, ..., Any], Group, ContextMenu]] = list(self._global_commands.values())
            #base.extend(cmd for ((_, g, _), cmd) in self._context_menus.items() if g is None)
            #return base
        #else:
            #try:
                #commands = self._guild_commands[guild.id]
            #except KeyError:
                #guild_id = guild.id
                #return [cmd for ((_, g, _), cmd) in self._context_menus.items() if g == guild_id]
            #else:
                #base: List[Union[Command[Any, ..., Any], Group, ContextMenu]] = list(commands.values())
                #guild_id = guild.id
                #base.extend(cmd for ((_, g, _), cmd) in self._context_menus.items() if g == guild_id)
                #return base



    #async def sync(self, *, guild: Optional[Snowflake] = None) -> List[AppCommand]:

        #if self.client.application_id is None:
            #raise MissingApplicationID
 
        #commands: List[Command[Any, (...), Any] | Group | ContextMenu] = self._get_all_commands(guild=guild)
        #translator = self.translator
        #print(guild.id)
        #lang = get_locale_lang(self.i18n.get_lang(guild.id))
        #if translator:
            #payload = [await command.get_translated_payload(translator, lang) for command in commands]
        #else:
            #payload = [command.to_dict() for command in commands]

        #try:
            #if guild is None:
                #data = await self._http.bulk_upsert_global_commands(self.client.application_id, payload=payload)
            #else:
                #data = await self._http.bulk_upsert_guild_commands(self.client.application_id, guild.id, payload=payload)
        #except HTTPException as e:
            #if e.status == 400:
                #raise CommandSyncFailure(e, commands) from None
            #raise

        #return [AppCommand(data=d, state=self._state) for d in data]






















class Translator(app_commands.Translator):
    def __init__(self) -> None:
        super().__init__()

        #self.default_lang = default_lang
        


    def __get_locale(self, locale: Locale) -> str | None:
        if locale == Locale.brazil_portuguese:
            return "pt"

        if locale == Locale.american_english or locale == Locale.british_english:
            return "en"

        return None 






    async def translate(self, string: app_commands.locale_str, locale: Locale, context: app_commands.TranslationContext) -> Optional[str]:
        # translate
        locale = self.__get_locale(locale)


        if not i18n.check_lang(locale):
            return None

        if context.location is TranslationContextLocation.command_name:

            cog = context.data.module.replace("cogs.", "")
            command_name = context.data.qualified_name.replace(" ", "_")
            translated_command_name = i18n.get_command_name(command_name, cog, locale)
            return translated_command_name

        if context.location is TranslationContextLocation.command_description:
            cog = context.data.module.replace("cogs.", "")
            command_name = context.data.qualified_name.replace(" ", "_")
            translated_command_description = i18n.get_command_description(command_name, cog, locale)
            return translated_command_description

        if context.location is TranslationContextLocation.group_name:
            cog = context.data.module.replace("cogs.", "")
            group_name = context.data.qualified_name.replace(" ", "_")
            translated_group_name = i18n.get_group_name(group_name, cog, locale)
            return translated_group_name

        if context.location is TranslationContextLocation.group_description:
            cog = context.data.module.replace("cogs.", "")
            group_description = context.data.qualified_name.replace(" ", "_")
            translated_group_description = i18n.get_group_description(group_description, cog, locale)
            return translated_group_description


        #if context.location is TranslationContextLocation.parameter_name:
            #return "parameter_name"

        #if context.location is TranslationContextLocation.parameter_description:
            #return "parameter_description"

        #if context.location is TranslationContextLocation.choice_name:
            #return "choice_name"

        #if context.location is TranslationContextLocation.other:
            #return "choice_value"




        #match context.location:
            #case TranslationContextLocation.command_name():
                #cog = context.data.module.replace("cogs.", "")
                #command_name = context.data.qualified_name.replace(" ", "_")
                #translated_command_name = i18n.get_command_name(command_name, cog, locale)
                #return translated_command_name
                

            #case TranslationContextLocation.command_description():
                #cog = context.data.module.replace("cogs.", "")
                #command_name = context.data.qualified_name.replace(" ", "_")
                #translated_command_description = i18n.get_command_description(command_name, cog, locale)
                #return translated_command_description

            #case TranslationContextLocation.group_name():
                #cog = context.data.module.replace("cogs.", "")
                #group_name = context.data.qualified_name.replace(" ", "_")
                #translated_group_name = i18n.get_group_name(group_name, cog, locale)
                #return translated_group_name

            #case TranslationContextLocation.group_description():
                #cog = context.data.module.replace("cogs.", "")
                #group_description = context.data.qualified_name.replace(" ", "_")
                #translated_group_description = i18n.get_group_description(group_description, cog, locale)
                #return translated_group_description


            #case TranslationContextLocation.parameter_name():
                #return "parameter_name"

            #case TranslationContextLocation.parameter_description():
                #return "parameter_description"

            #case TranslationContextLocation.choice_name():
                #return "choice_name"

            #case TranslationContextLocation.other():
                #return "choice_value"



        
        #if context.location is not TranslationContextLocation.parameter_name and context.location is not TranslationContextLocation.parameter_description:
            #print(context.data.module)

        #if context.location is TranslationContextLocation.parameter_name:
            #print(context.data.command.__dict__)


        #print(context.data)
        #print(context.location)

        return None
