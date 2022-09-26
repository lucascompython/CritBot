import discord
from discord import errors
from discord.ext import commands

import asyncio
from typing import Optional, Union


class Fun(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        


    @commands.hybrid_command()
    async def spam(self, ctx, mbr: Union[discord.Member, discord.User], number: int, *, message: str) -> None:

        if number > 100:
            return await ctx.send(self.t("err", "dont_be_a_dick"))
        await ctx.send(self.t("cmd", "spamming", user=mbr))

        try:
            for _ in range(number):
                await mbr.send(message)
                await asyncio.sleep(1)
        except errors.HTTPException:
            return await ctx.send(self.t("err", "cant_send", user=mbr))
        
        await ctx.send(self.t("cmd", "output", user=mbr))


    @commands.hybrid_command(aliases=["acorda"])
    async def wake(self, ctx, mbr: Union[discord.Member, discord.User], channel: Union[discord.VoiceChannel, discord.StageChannel], number: int, *, reason: Optional[str]) -> None:
        if number > 50:
            return await ctx.send(self.t("err", "dont_be_a_dick"))
        author_channel = ctx.author.voice.channel

        await ctx.send(self.t("cmd", "waking", user=mbr))
        for _ in range(number):
            await mbr.move_to(channel, reason=reason)
            await mbr.move_to(author_channel, reason=reason)
        
        await ctx.send(self.t("cmd", "output", user=mbr))


        






        
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("Fun")