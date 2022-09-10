from aiofiles import open as async_open

import os, json


class I18n:
    def __init__(self) -> None:
        self.path_to_langs = "./i18n/langs.json"
        self.path_to_translations = "./config/translations/"
        self.translations = {}

        self.guild_id = None
        self.cog_name = None
        self.command_name = None

        self.accepted_langs = {
            "pt": ["portuguese", "português"],
            "en": ["english", "inglês"]
        }

        #load the file that contains the guilds and their languages
        with open(self.path_to_langs, "r") as f:
            self.langs = json.load(f)
            

        #load all translations
        for file_name in [file for file in os.listdir(self.path_to_translations) if file.endswith('.json')]:
            with open(self.path_to_translations + file_name) as json_file:
                self.translations[file_name[:-5]] = json.load(json_file)

    def check_lang(self, lang: str) -> bool:
        return lang in self.accepted_langs or lang in self.accepted_langs.values()

    def t(self, *args, **kwargs) -> str:
        return self.get_key_string(
            self.get_lang(self.guild_id),
            self.cog_name,
            *args
        ).format(**kwargs)

    async def reload_translations(self) -> None:
        for file_name in [file for file in os.listdir(self.path_to_translations) if file.endswith('.json')]:
            async with async_open(self.path_to_translations + file_name) as f:
                contents = await f.read()
            self.translations[file_name[:-5]] = json.loads(contents)


    def get_key_string(self, lang: str, cog: str, *args) -> str:
        #args = list(args)
        #args[1:1] = [self.command_name]
        #key_string = "-".join(args)
        #print(key_string)
        try:
            return self.get_keys_string(lang, cog)[self.command_name]["-".join(args)]
        except KeyError:
            # if not implemented in the language, return the english version
            return self.get_keys_string("en", cog)[self.command_name]["-".join(args)]

    def get_keys_string(self, lang: str, cog: str) -> dict:
        return self.translations[lang + "." + cog]

    def get_lang(self, guild_id: int) -> str:
        return self.langs[str(guild_id)]
    


    async def update_langs(self, guild_id: int, lang: str) -> None:
        try:
            if self.langs[str(guild_id)] == lang:
                raise ValueError("The language is the same as the current one")
        except KeyError:
            pass

        self.langs[str(guild_id)] = lang
        async with async_open("./i18n/langs.json", "w") as f:
            await f.write(json.dumps(self.langs, indent=4))


    async def delete_lang(self, guild_id: int) -> None:
        self.langs.pop(str(guild_id))
        async with async_open("./i18n/langs.json", "w") as f:
            await f.write(json.dumps(self.langs, indent=4))