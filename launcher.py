#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
from dataclasses import dataclass
from argparse import ArgumentParser
from time import sleep

import asyncpg
import aiofiles
import aiofiles.os
import discord
import uvloop
from aiohttp import ClientSession
from colorlog import ColoredFormatter
from discord import app_commands
from discord.ext import commands

from bot import CritBot
from config import data
from i18n import I18n

lavalink_proc: subprocess.Popen[bytes] = None


@dataclass
class Colors:
    red: str = "\033[31m"
    green: str = "\033[32m"
    yellow: str = "\033[33m"
    blue: str = "\033[34m"
    purple: str = "\033[35m"
    cyan: str = "\033[36m"
    white: str = "\033[37m"
    bold: str = "\033[1m"
    reset: str = "\033[0m"


async def start_bot(dev: bool) -> None:
    if dev:
        print("Running in development mode...")
        data["dev"] = True
    else:
        print("Running in production mode...")
        data["dev"] = False

    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename="./logs/discord.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,
    )
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = ColoredFormatter(
        "[{asctime}] {log_color}[{levelname:<8}]{reset}{purple} {name}{reset}: {blue}{message}{reset}",
        dt_fmt,
        style="{",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    async with ClientSession() as our_client, asyncpg.create_pool(
        **data["postgres"]
    ) as pool:
        exts = [
            f"cogs.{file[:-3]}" for file in os.listdir("./cogs") if file.endswith(".py")
        ]

        # Apply migrations
        files = await aiofiles.os.listdir("./migrations")
        for file in files:
            async with aiofiles.open(f"./migrations/{file}", "r") as f:
                migration = await f.read()
                await pool.execute(migration)
                logger.log(20, f"Applied migration {file}")

        async with pool.acquire() as conn:
            prefixes_and_langs: list[asyncpg.Record] = await conn.fetch(
                "SELECT id, prefix, lang FROM guilds"
            )

        prefixes: dict[int, str] = {}
        langs: dict[int, str] = {}
        for record in prefixes_and_langs:
            prefixes[record["id"]] = record["prefix"]
            langs[record["id"]] = record["lang"]

        async def get_prefix(bot, message):
            return commands.when_mentioned_or(prefixes[message.guild.id])(bot, message)

        i18n = I18n(
            data["default_language"],
            data["dev"],
            data["testing_guild_id"],
            langs,
        )

        class CritTree(app_commands.CommandTree):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

            async def interaction_check(self, interaction, /) -> bool:
                if "hybrid" not in str(interaction.command):
                    i18n.guild_id = interaction.guild_id
                    i18n.cog_name = interaction.command.extras["cog_name"]
                    i18n.command_name = interaction.command.qualified_name.replace(
                        " ", "_"
                    )
                return True

        async with CritBot(
            i18n=i18n,
            prefixes=prefixes,
            web_client=our_client,
            initial_extensions=exts,
            db_pool=pool,
            **data,
            intents=discord.Intents.all(),
            command_prefix=get_prefix,
            case_insensitive=True,
            strip_after_prefix=True,
            tree_cls=CritTree,
        ) as bot:
            await bot.start(data["discord_token"], reconnect=True)


class Lavalink:
    __slots__ = ("lavalink", "path", "ip", "port", "path", "run_lavalink_command")

    default_lavalink_ip = "0.0.0.0"
    default_lavalink_port = "2333"
    default_lavalink = default_lavalink_ip + ":" + default_lavalink_port
    default_lavalink_path = "./config/Lavalink.jar"

    def __init__(self, lavalink: str | None, path: str | None) -> None:
        self.lavalink = lavalink
        self.path = path

        self.ip = None
        self.port = None
        if self.lavalink:
            self.ip = lavalink.split(":")[0]
            self.port = lavalink.split(":")[1]

        # TODO fix run lavalink
        self.run_lavalink_command = (
            lambda p=None: ["java", "-jar", self.default_lavalink_path]
            if not p
            else ["java", "-jar", p]
        )

    def start_lavalink(self) -> None:
        global lavalink_proc, data

        if (data_path := data["lavalink"]["path"]) or self.path or not self.lavalink:
            if data_path and not self.lavalink:
                self.path = data_path
            if self.lavalink:
                return
            lavalink_proc = subprocess.Popen(
                self.run_lavalink_command(self.path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            sleep(2.5)  # Make sure Lavalink has time to start up

        data["lavalink"]["path"] = self.path
        data["lavalink"]["ip"] = self.ip if self.ip else self.default_lavalink_ip
        data["lavalink"]["port"] = (
            self.port if self.port else self.default_lavalink_port
        )


def arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="The launcher for the bot.")
    parser.add_argument(
        "-l",
        "--lavalink",
        help=f"IP and Port to Lavalink: <ip>:<port>. Default: {Lavalink.default_lavalink}",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-p",
        "--path",
        help=f"Path to Lavalink. Default: {Lavalink.default_lavalink_path}",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-d",
        "--dev",
        help="Run the bot in development mode.",
        action="store_true",
        required=False,
        default=False,
    )

    return parser.parse_args()


async def main(args: ArgumentParser) -> None:
    print("Starting bot...")
    if args.lavalink:
        print(f"Connecting to Lavalink at {args.lavalink}")
    else:
        print("Starting Lavalink...")
    lavalink = Lavalink(args.lavalink, args.path)
    lavalink.start_lavalink()
    await start_bot(args.dev)


if __name__ == "__main__":
    try:
        args = arg_parser()
        uvloop.run(main(args), debug=args.dev)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        exit(0)
    finally:
        if lavalink_proc:
            print("\nKilling Lavalink...")
            lavalink_proc.terminate()
        print("Exiting...")


else:
    print("This script is not meant to be imported! You little cunt")
    exit(1)
