import asyncio
import datetime
import logging
import logging.handlers
import time
from collections import deque
from typing import Optional

import asyncpg
import asyncpraw
import discord
import wavelink
from aiohttp import ClientSession
from discord.ext import commands, tasks

from i18n import I18n, Translator
from Utils import CritHelpCommand


class CritBot(commands.Bot):
    def __init__(
        self,
        *args,
        i18n: I18n,
        prefixes: dict[int, str],
        web_client: ClientSession,
        initial_extensions: list[str],
        db_pool: asyncpg.Pool,
        source_link: str,
        invite_link: str,
        default_prefix: str,
        default_language: str,
        testing_guild_id: int,
        owner_id: int,
        lavalink: dict[str, str],
        dev: bool,
        genius_token: str,
        spotify_cred: dict[str, str],
        reddit_cred: dict[str, str],
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
        self.owner_id = owner_id
        self.__start_time = time.time()
        self.dev = dev
        self.genius_token = genius_token
        self.spotify_cred = spotify_cred
        self.reddit_cred = reddit_cred

        self.submissions = []
        self.reddit: asyncpraw.Reddit = None

        self.db_pool = db_pool

        self.used_commands: dict[str, int] = {}  # command name: times used

        # i18n
        self.default_language = default_language
        self.i18n = i18n

        self.wavelink_node: wavelink.Node = None

        if self.dev:
            self.last_cmds = deque(maxlen=10)  # cache the 10 last commands

    # TODO if all the commands can be hybrid command check the new (2.1 feature) interaction.translate to translate per user locale instead of per guild locale

    async def get_reddit_submissions(self) -> asyncpraw.Reddit:
        async with asyncpraw.Reddit(**self.reddit_cred) as reddit:
            reddit.read_only = True

            subreddit = await reddit.subreddit("memes")

            async for submission in subreddit.top(limit=100, time_filter="week"):
                self.submissions.append(submission)

        self.reddit = reddit

    async def setup_hook(self) -> None:
        translator = Translator(i18n=self.i18n)
        await asyncio.gather(
            self.get_reddit_submissions(),
            self.tree.set_translator(translator),
        )

        self.help_command = CritHelpCommand(i18n=self.i18n, slash=False)

        # Initiate the lavalink client
        self.node = wavelink.Node(
            uri=self.lavalink["ip"] + ":" + self.lavalink["port"],
            password=self.lavalink["password"],
        )
        nodes = [self.node]

        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

        self.logger.log(20, "Loading the cogs.")
        # load all cogs in ./cogs
        for extension in self.initial_extensions:
            if (
                not self.dev and extension == "cogs.dev"
            ):  # only load dev cog if the bot is in dev mode
                continue

            await self.load_extension(extension)
            self.cogs_state["loaded"].append(extension.replace("cogs.", ""))
        self.logger.log(20, "Cogs loaded.")

        self.logger.log(20, "Syncing the bot.")
        guild = discord.Object(self.testing_guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        # await self.tree.sync() # syncs all guilds takes a longe time
        self.logger.log(20, "Syncing done!")

        self.batch_update_commands.start()

    async def on_ready(self) -> None:
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/help",
            )
        )
        self.add_check(
            self.set_guild_and_cog_and_command
        )  # adds a fake check to all commands to set the guild id and the cog name
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

    async def update_prefixes(
        self, guild_id: int, new_prefix: str, ctx: Optional[commands.Context] = None
    ) -> None:
        """This function updates the prefixes in the database and in the prefixes dict

        Args:
            guild_id (int): The guild id
            new_prefix (str): The new prefix
            ctx (Optional[commands.Context], optional): If provided the function will send the output message to the context's channel. Defaults to None.
        """
        try:
            if self.prefixes[guild_id] == new_prefix:
                if ctx:
                    await ctx.send(
                        self.i18n.t("err", "same_prefix", prefix=new_prefix, ctx=ctx)
                    )
                    return
        except KeyError:
            # if the guild is not in the database yet probably because it's a new guild from a new server
            pass

        self.prefixes[guild_id] = new_prefix

        # update in the database
        async with self.db_pool.acquire() as conn:
            if ctx:
                await asyncio.gather(
                    conn.execute(
                        "INSERT INTO guilds (id, prefix) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET prefix = excluded.prefix;",
                        guild_id,
                        new_prefix,
                    ),
                    ctx.send(self.i18n.t("cmd", "output", prefix=new_prefix, ctx=ctx)),
                )
            else:
                await conn.execute(
                    "INSERT INTO guilds (id, prefix) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET prefix = excluded.prefix;",
                    guild_id,
                    new_prefix,
                )

    async def reload_prefixes(self) -> None:
        """Reloads from the database
        Only use case when the developer changes manually the prefixes"""

        async with self.db_pool.acquire() as conn:
            self.prefixes = await conn.fetch(
                "SELECT id, prefix FROM guilds WHERE prefix IS NOT NULL;"
            )

    async def set_guild_and_cog_and_command(self, ctx) -> bool:
        """Sets the guild id and the cog name to i18n"""
        self.i18n.guild_id = ctx.guild.id
        self.i18n.cog_name = ctx.cog.__class__.__name__.lower()
        self.i18n.command_name = ctx.command.qualified_name.replace(" ", "_")
        if self.dev and self.i18n.command_name != "!!":
            self.last_cmds.append(ctx.message.content)

        self.used_commands[ctx.command.qualified_name] = (
            self.used_commands.get(ctx.command.qualified_name, 0) + 1
        )
        return True

    @tasks.loop(minutes=5.0)
    async def batch_update_commands(self) -> None:
        # TODO: add the guild specific commands to the database
        """Updates the number of time a command has been used to the database"""
        if any(value for value in self.used_commands.values()):
            async with self.db_pool.acquire() as conn:
                for command, count in self.used_commands.items():
                    query = """
                    INSERT INTO commands (name, number) VALUES ($1, $2)
                    ON CONFLICT (name) DO UPDATE SET number = commands.number + excluded.number;
                    """
                    await conn.execute(query, command, count)

            self.used_commands.clear()  # clear the dict after updating the database so if a command isn't used it won't be updated

    @property
    def uptime(self) -> str:
        """Returns the bot's uptime"""
        return str(
            datetime.timedelta(seconds=int(round(time.time() - self.__start_time)))
        )
