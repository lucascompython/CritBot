import discord
from discord.ext import commands


import json, os, asyncio, logging, yaml
import logging.handlers
from typing import List
from aiohttp import ClientSession



class CritBot(commands.Bot):
    def __init__(
        self,
        *args,
        default_prefix: str = ".",
        prefixes: dict[str, str],
        initial_extensions: List[str],
        web_client: ClientSession,
        testing_guild_id: int,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.web_client = web_client
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = initial_extensions
        self.logger = logging.getLogger("discord")
        self.cogs_state: dict[str, list[str]] = {"loaded": [], "unloaded": []}
        self.default_prefix = "."
        self.prefixes = prefixes
        

    async def setup_hook(self) -> None:
        
        for extension in self.initial_extensions:
            await self.load_extension(extension)
            self.cogs_state["loaded"].append(extension.replace("cogs.", ""))

        guild = discord.Object(self.testing_guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        #await self.tree.sync() # syncs all guilds takes a longe time
        print("Syncing done!")


    async def change_activity(self) -> None:
        """Changes the bot's activity"""
        #puts a button on the activity
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

        self.logger.log(20, f"Logado como {self.user}!")


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

    def update_prefixes(self, guild_id: int, new_prefix: str) -> None:
        """Updates the prefixes.json file with the new prefix"""
        self.prefixes[str(guild_id)] = new_prefix
        with open("./prefixes.json", "w") as f:
            json.dump(self.prefixes, f, indent=4)
        
    def delete_prefix(self, guild_id: int) -> None:
        """Deletes the prefix for the guild"""
        self.prefixes.pop(str(guild_id))
        with open("./prefixes.json", "w") as f:
            json.dump(self.prefixes, f, indent=4)
        
async def main():
    print("Starting bot!")
    with open("./appsettings.yaml", "r") as f:
        data = yaml.safe_load(f)

    with open("./prefixes.json", "r") as f:
        prefixes = json.load(f)
    
    def get_prefix(bot, message):
        return prefixes[str(message.guild.id)]


    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename="discord.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024, # 32 MiB
        backupCount=5,
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    



    async with ClientSession() as our_client:
        
        exts = []
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                exts.append(f"cogs.{filename[:-3]}")
    
        async with CritBot(defualt_prefix=data["default_prefix"],
                prefixes=prefixes,
                web_client=our_client,
                initial_extensions=exts,
                testing_guild_id=data["testing_guild_id"],
                intents=discord.Intents.all(),
                command_prefix=get_prefix,
                case_insensitive=True,
                description="Bruh",
                owner_id=data["owner_id"],
                strip_after_prefix=True
            ) as bot:
                await bot.start(data["discord_token"], reconnect=True)


if __name__ == "__main__":
    asyncio.run(main())
else:
    print("\nJust die...")
