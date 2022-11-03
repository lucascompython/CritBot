import orjson
import discord
from discord.ext import commands
from aiohttp import ClientSession
from aiofiles import open as async_open


import json
import logging
import logging.handlers


from i18n import Translator

class CritBot(commands.Bot):
    def __init__(
        self,
        *args,
        i18n,
        prefixes: dict[str, str],
        web_client: ClientSession,
        initial_extensions: list[str],
        source_link: str,
        invite_link: str,
        default_prefix: str,
        default_language: str,
        testing_guild_id: int,
        lavalink: dict[str, str | int],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions
        self.logger = logging.getLogger("discord")
        self.cogs_state: dict[str, list[str]] = {"loaded": [], "unloaded": []}
        self.default_prefix = default_prefix
        self.prefixes = prefixes
        self.invite_link = invite_link
        self.source_link = source_link
        self.lavalink = lavalink
        
        # i18n
        self.default_language = default_language
        self.i18n = i18n
        

    async def setup_hook(self) -> None:
        
        self.logger.log(20, "Setting up the translator.")
        await self.tree.set_translator(Translator)
        self.logger.log(20, "Translator set up")


        self.logger.log(20, "Loading the cogs.")
        # load all cogs in ./cogs
        for extension in self.initial_extensions:
            await self.load_extension(extension)
            self.cogs_state["loaded"].append(extension.replace("cogs.", ""))
        self.logger.log(20, "Cogs loaded.")



        self.logger.log(20, "Syncing the bot.")
        guild = discord.Object(self.testing_guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        #await self.tree.sync() # syncs all guilds takes a longe time
        self.logger.log(20, "Syncing done!")


    async def change_activity(self) -> None:
        """Changes the bot's activity"""
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.default_prefix}help",
            )
        )





    async def on_ready(self) -> None:
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{self.default_prefix}help",
            )
        )
        self.add_check(self.set_guild_and_cog_and_command) # adds a fake check to all commands to set the guild id and the cog name
        self.logger.log(20, f"Logged as {self.user}!")


    async def change_cogs_state(self, mode: str, cog: str) -> None:
        if mode == "load":
            await self.load_extension(f"cogs.{cog}")
            try:
                self.cogs_state["unloaded"].remove(cog)
            except ValueError:
                # if the cog is new and not in the unloaded list yet
                pass
            self.cogs_state["loaded"].append(cog)
        elif mode == "unload":
            await self.unload_extension(f"cogs.{cog}")
            self.cogs_state["loaded"].remove(cog)
            self.cogs_state["unloaded"].append(cog)
        else:
            raise ValueError("Invalid mode")

    async def update_prefixes(self, guild_id: int, new_prefix: str) -> None:
        """Updates the prefixes.json file with the new prefix"""
        try:
            if self.prefixes[str(guild_id)] == new_prefix:
                raise ValueError("The new prefix is the same as the old one")
        except KeyError:
            # if the guild is not in the prefixes.json file yet probably because it's a new guild from a new server
            pass

        self.prefixes[str(guild_id)] = new_prefix
        async with async_open("./prefixes.json", mode="w") as f:
            # write json async
            await f.write(json.dumps(self.prefixes, indent=4))
        
    async def delete_prefix(self, guild_id: int) -> None:
        """Deletes the prefix for the guild"""
        self.prefixes.pop(str(guild_id))
        async with async_open("./prefixes.json", "w") as f:
            await f.write(json.dumps(self.prefixes, indent=4))

    async def reload_prefixes(self) -> None:
        """Reloads from the prefixes.json file
        Only use case when the developer changes manually the prefixes"""
        async with async_open("./prefixes.json", "r") as f:
            self.prefixes = orjson.loads(await f.read())

    async def set_guild_and_cog_and_command(self, ctx) -> bool:
        """Sets the guild id and the cog name to i18n"""
        self.i18n.guild_id = ctx.guild.id
        self.i18n.cog_name = ctx.cog.__class__.__name__.lower()
        self.i18n.command_name = ctx.command.qualified_name.replace(" ", "_")
        return True
            
        
