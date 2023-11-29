from typing import Optional

import discord
from discord import app_commands
import wavelink
from discord.ext import commands
import asyncio

# import the bot class from bot.py
from bot import CritBot
from Utils import GeniusLyrics, Paginator, SongNotFound
from enum import Enum


class Platform(Enum):
    YOUTUBE = ("youtube", "yt")
    SPOTIFY = ("spotify", "sp")
    SOUNDCLOUD = ("soundcloud", "sc")
    YOUTUBE_MUSIC = ("youtube_music", "ytm")

    @classmethod
    def from_string(cls, value: str) -> "Platform":
        for platform in cls:
            if value.lower() in platform.value:
                return platform
        return cls.YOUTUBE  # default to Youtube if no match is found

    def __str__(self) -> str:
        return self.value[0]


class Music(commands.Cog):
    def __init__(self, bot: CritBot):
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log

    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))


async def teardown(bot) -> None:
    await bot.remove_cog("Music")
