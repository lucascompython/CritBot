from discord.ext import commands
import discord
import wavelink
from bot import CritBot
import asyncio


class Config(commands.Cog):
    """Manage the bot's configuration."""

    def __init__(self, bot: CritBot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        self.sponsorblock_categories = [
            "sponsor",
            "selfpromo",
            "interaction",
            "intro",
            "outro",
            "preview",
            "music_offtopic",
            "filler",
        ]

    @commands.hybrid_command(aliases=["mudar_prefixo", "prefixo", "prefix"])
    async def change_prefix(self, ctx, prefix) -> None:
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
    async def change_language(self, ctx, lang) -> None:
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

    async def get_active_sponsorblock_categories(self, guild_id: int) -> list[str]:
        # return await self.bot.wavelink_node.send(
        #     "GET",
        #     path=f"v4/sessions/{self.bot.wavelink_node.session_id}/players/{guild_id}/sponsorblock/categories",
        # )

        pool = self.bot.db_pool

        async with pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT sponsorblock_categories FROM guilds WHERE id = $1;",
                guild_id,
            )

    async def sponsorblock_show_logic(self, ctx: commands.Context) -> None:
        active_categories = await self.get_active_sponsorblock_categories(ctx.guild.id)

        active_categories_str = ""

        for category in self.sponsorblock_categories:
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

    @commands.hybrid_group(aliases=["sb", "sponsor"])
    async def sponsorblock(
        self,
        ctx: commands.Context,
    ) -> None:
        if ctx.invoked_subcommand is None:
            await self.sponsorblock_show_logic(ctx)

    @sponsorblock.command(name="show", aliases=["mostrar"])
    async def sponsorblock_show(self, ctx: commands.Context) -> None:
        await self.sponsorblock_show_logic(ctx)

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))

    @sponsorblock.command(name="enable", aliases=["ativar"])
    async def sponsorblock_enable(self, ctx: commands.Context, category: str) -> None:
        if category not in self.sponsorblock_categories:
            await ctx.reply(
                self.t(
                    "err",
                    "invalid_category",
                    category=category,
                )
            )
            return

        if category in await self.get_active_sponsorblock_categories(ctx.guild.id):
            await ctx.reply(
                self.t(
                    "err",
                    "already_enabled",
                    category=category,
                )
            )
            return

        node = self.bot.wavelink_node
        await node.send(
            "PUT",
            path=f"v4/sessions/{node.session_id}/players/{ctx.guild.id}/sponsorblock/categories",
            data=[category],
        )
        await ctx.send(self.t("cmd", "output", category=category))


async def setup(bot) -> None:
    await bot.add_cog(Config(bot))


async def teardown(bot) -> None:
    await bot.remove_cog("Config")
