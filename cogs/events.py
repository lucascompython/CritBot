import traceback
from bot import CritBot

from discord.ext import commands
import asyncio
import discord

from Utils import SponsorBlockCache


class Events(commands.Cog):
    def __init__(self, bot: CritBot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.bot.sponsorblock_cache[guild.id] = SponsorBlockCache(
            active_categories=self.bot.sponsorblock_default_categories,
            print_segment_skipped=True,
        )
        async with self.bot.db_pool.acquire() as conn:
            await asyncio.gather(
                self.bot.update_prefixes(guild.id, self.bot.default_prefix),
                self.bot.i18n.update_langs(guild.id, self.bot.default_language, conn),
            )

        self.log(20, f"Joined {guild.name} ({guild.id})")
        self.bot.tree.copy_global_to(guild=guild)
        await self.bot.tree.sync(guild=guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        self.bot.prefixes.pop(guild.id)
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM guilds WHERE id = $1", guild.id)
        self.log(20, f"Left {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.bot.i18n.command_name = "on_command_error"
        self.bot.i18n.cog_name = "events"
        self.bot.i18n.guild_id = ctx.guild.id

        # TODO add more errors like when the arguments are of the wrong type
        if isinstance(error, commands.NotOwner):
            await ctx.reply(self.t("err", "not_owner"))

        if isinstance(error, commands.CommandNotFound):
            pass
        else:
            await ctx.reply(self.t("err", "unknown"))
            self.log(40, error)
            traceback.print_exception(type(error), error, error.__traceback__)

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot) -> None:
    await bot.add_cog(Events(bot))


async def teardown(bot) -> None:
    await bot.remove_cog("Events")
