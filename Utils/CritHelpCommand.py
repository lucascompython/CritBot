import discord
from discord.ext import commands


class CritHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Bot help")
        # `mapping` is a dict of the bot's cogs, which map to their commands
        for cog, cmds in mapping.items():  # get the cog and its commands separately
            embed.add_field(
                name = cog.qualified_name,       # get the cog name
                value = f"{len(cmds)}"  # get a count of the commands in the cog.
            )
            
        channel = self.get_destination()  # this method is inherited from `HelpCommand`, and gets the channel in context
        await channel.send(embed=embed)
