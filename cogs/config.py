import asyncio

import discord
from discord.ext import commands

from bot import CritBot
from Utils import BoolConverter


class Config(commands.Cog):
    """Manage the bot's configuration."""

    def __init__(
        self,
        bot: CritBot,
    ) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

    @commands.hybrid_command(aliases=["mudar_prefixo", "prefixo", "prefix"])
    async def change_prefix(self, ctx: commands.Context, prefix: str) -> None:
        await self.bot.update_prefixes(
            ctx.guild.id, prefix, ctx
        )  # This will automagically send the output/error message to the channel

    @commands.hybrid_command(
        aliases=[
            "change_lang",
            "mudar_idioma",
            "mudar_linguagem",
            "mudar_lingua",
            "mudar_língua",
            "idioma",
            "language",
        ]
    )
    async def change_language(self, ctx: commands.Context, lang: str) -> None:
        """Change the bot language."""
        if self.bot.i18n.check_lang(lang):
            async with self.bot.db_pool.acquire() as conn:
                await self.bot.i18n.update_langs(
                    ctx.guild.id, lang, conn, ctx
                )  # This will automagically send the output/error message to the channel
        else:
            await ctx.send(
                self.t(
                    "err",
                    "invalid_language",
                    lang=lang,
                    langs=", ".join(self.bot.i18n.accepted_langs),
                )
            )

    async def sponsorblock_show_logic(self, ctx: commands.Context) -> None:
        active_categories = self.bot.sponsorblock_cache[ctx.guild.id].active_categories

        active_categories_str = ""

        for category in self.bot.sponsorblock_categories:
            if category in active_categories:
                active_categories_str += f":white_check_mark:  {category}\n"
            else:
                active_categories_str += f":x:  {category}\n"

        embed = discord.Embed(
            title=self.t("embed", "description", mcommand_name="sponsorblock"),
            description=active_categories_str,
        )
        embed.set_author(
            icon_url="https://sponsor.ajay.app/LogoSponsorBlockSimple256px.png",
            name=self.t("embed", "title"),
            url="https://wiki.sponsor.ajay.app/w/Guidelines",
        )
        embed.set_footer(text=self.t("embed", "footer"))
        await ctx.send(embed=embed)

    @commands.hybrid_group(name="sponsorblock", aliases=["sb", "sponsor"])
    async def _sponsorblock(
        self,
        ctx: commands.Context,
    ) -> None:
        if ctx.invoked_subcommand is None:
            await self.sponsorblock_show_logic(ctx)

    @_sponsorblock.command(name="show", aliases=["mostrar"])
    async def sponsorblock_show(self, ctx: commands.Context) -> None:
        await self.sponsorblock_show_logic(ctx)

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))

    @_sponsorblock.command(name="enable", aliases=["ativar"])
    async def sponsorblock_enable(self, ctx: commands.Context, category: str) -> None:
        if category not in self.bot.sponsorblock_categories:
            await ctx.reply(
                self.t(
                    "err",
                    "invalid_category",
                    category=category,
                )
            )
            return

        category = category.lower()

        if category in self.bot.sponsorblock_cache[ctx.guild.id].active_categories:
            await ctx.reply(
                self.t(
                    "err",
                    "already_enabled",
                    category=category,
                )
            )
            return

        self.bot.sponsorblock_cache[ctx.guild.id].active_categories.append(category)
        await asyncio.gather(
            ctx.send(self.t("cmd", "output", category=category)),
            self.bot.sponsorblock.update_categories(
                ctx.guild.id,
                self.bot.sponsorblock_cache[ctx.guild.id].active_categories,
                self.bot.wavelink_node,
            ),
        )

    @_sponsorblock.command(name="disable", aliases=["desativar"])
    async def sponsorblock_disable(self, ctx: commands.Context, category: str) -> None:
        if category not in self.bot.sponsorblock_categories:
            await ctx.reply(
                self.t(
                    "err",
                    "invalid_category",
                    category=category,
                )
            )
            return

        category = category.lower()

        if category not in self.bot.sponsorblock_cache[ctx.guild.id].active_categories:
            await ctx.reply(
                self.t(
                    "err",
                    "already_disabled",
                    category=category,
                )
            )
            return

        self.bot.sponsorblock_cache[ctx.guild.id].active_categories.remove(category)
        await asyncio.gather(
            ctx.send(self.t("cmd", "output", category=category)),
            self.bot.sponsorblock.update_categories(
                ctx.guild.id,
                self.bot.sponsorblock_cache[ctx.guild.id].active_categories,
                self.bot.wavelink_node,
            ),
        )

    @_sponsorblock.command(
        name="toggle", aliases=["alternar"], help="Toggle a category"
    )
    async def sponsorblock_toggle(self, ctx: commands.Context, category: str) -> None:
        if category not in self.bot.sponsorblock_categories:
            await ctx.reply(
                self.t(
                    "err",
                    "invalid_category",
                    category=category,
                    mcommand_name="sponsorblock_enable",
                )
            )
            return

        category = category.lower()

        if category in self.bot.sponsorblock_cache[ctx.guild.id].active_categories:
            self.bot.sponsorblock_cache[ctx.guild.id].active_categories.remove(category)
            await asyncio.gather(
                ctx.send(
                    self.t(
                        "cmd",
                        "output",
                        category=category,
                        mcommand_name="sponsorblock_disable",
                    )
                ),
                self.bot.sponsorblock.update_categories(
                    ctx.guild.id,
                    self.bot.sponsorblock_cache[ctx.guild.id].active_categories,
                    self.bot.wavelink_node,
                ),
            )
        else:
            self.bot.sponsorblock_cache[ctx.guild.id].active_categories.append(category)
            await asyncio.gather(
                ctx.send(
                    self.t(
                        "cmd",
                        "output",
                        category=category,
                        mcommand_name="sponsorblock_enable",
                    )
                ),
                self.bot.sponsorblock.update_categories(
                    ctx.guild.id,
                    self.bot.sponsorblock_cache[ctx.guild.id].active_categories,
                    self.bot.wavelink_node,
                ),
            )

    @_sponsorblock.command(name="print", aliases=["mensagem", "message"])
    async def sponsorblock_print(
        self, ctx: commands.Context, value: BoolConverter
    ) -> None:
        self.bot.sponsorblock_cache[ctx.guild.id].print_segment_skipped = value
        await asyncio.gather(
            ctx.send(self.t("cmd", "printing" if value else "not_printing")),
            self.bot.sponsorblock.update_print_segment_skipped(ctx.guild.id, value),
        )


async def setup(bot: CritBot) -> None:
    await bot.add_cog(Config(bot))


async def teardown(bot: CritBot) -> None:
    await bot.remove_cog("Config")
