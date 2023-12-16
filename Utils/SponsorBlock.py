from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from wavelink import Node
import asyncio

if TYPE_CHECKING:
    from bot import CritBot


class SponsorBlockCategories(Enum):
    SPONSOR = "sponsor"
    SELFPROMO = "selfpromo"
    INTERACTION = "interaction"
    INTRO = "intro"
    OUTRO = "outro"
    PREVIEW = "preview"
    MUSIC_OFFTOPIC = "music_offtopic"
    FILLER = "filler"


@dataclass(slots=True)
class SponsorBlockCache:
    active_categories: list[SponsorBlockCategories]
    print_segment_skipped: bool


class SponsorBlock:
    def __init__(self, bot: "CritBot") -> None:
        self.bot = bot

    async def get_cache(self) -> dict[int, SponsorBlockCache]:
        """Query the database and return a dict with the guild id as key and a SponsorBlockCache object as value.

        Returns:
            dict[int, SponsorblockCache]: A dict with the guild id as key and a SponsorBlockCache object as value.
        """
        async with self.bot.db_pool.acquire() as conn:
            sposnorblock_config = await conn.fetch(
                "SELECT id, sponsorblock_categories, sponsorblock_print_segment_skipped FROM guilds;"
            )

        sponsorblock_cache: dict[int, SponsorBlockCache] = {}

        for record in sposnorblock_config:
            sponsorblock_cache[record["id"]] = SponsorBlockCache(
                active_categories=record["sponsorblock_categories"],
                print_segment_skipped=record["sponsorblock_print_segment_skipped"],
            )

        return sponsorblock_cache

    async def __update_categories_db(
        self, guild_id: int, categories: list[str]
    ) -> None:
        """Update the guild's sponsorblock categories in the database.

        Args:
            guild_id (int): The guild id.
            categories (list[str]): The categories to be updated.
        """
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE guilds SET sponsorblock_categories = $1 WHERE id = $2;",
                categories,
                guild_id,
            )

    async def update_categories(
        self, guild_id: int, categories: list[str], node: Node
    ) -> None:
        """Update the guild's sponsorblock categories.

        Args:
            guild_id (int): The guild id.
            categories (list[str]): The categories to be updated.
            node (Node): The wavelink node.
        """

        await asyncio.gather(
            self.__update_categories_db(guild_id, categories),
            node.send(
                "PUT",
                path=f"v4/sessions/{node.session_id}/players/{guild_id}/sponsorblock/categories",
                data=categories,
            ),
        )

    async def update_print_segment_skipped(self, guild_id: int, value: bool) -> None:
        """Update the guild's sponsorblock print segment skipped.

        Args:
            guild_id (int): The guild id.
            value (bool): The value to be updated.
        """

        async with self.bot.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE guilds SET sponsorblock_print_segment_skipped = $1 WHERE id = $2;",
                value,
                guild_id,
            )
