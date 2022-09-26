import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import locale_str as _T

import os, sys
from typing import Optional


#command_attres=dict(hidden=True)
class Dev(commands.Cog):
    """Classe que define comandos que apenas o desenvolvedor pode usar."""
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log


    async def set_cog(self, mode: str, input_cogs: Optional[list[str]] = None) -> str:
        """Set cog(s) to a certain state (loaded, unloaded or reload)

        Args:
            mode (str): Mode can me either load, unload or reload
            input_cogs (list[str] | None, optional): List of cogs to set IF none will do the action to all the available cogs. Defaults to None.

        Returns:
            str: Message accumulated by all the actions done
        """
        
        
        if mode != "reload":
            adjective = mode + "ed"
            contrary = lambda adj: "load" if adj == "unload" else "unload"
            contrary_adjective = contrary(mode) + "ed"

        cogs = input_cogs or (self.bot.cogs_state[contrary_adjective] if mode != "reload" else self.bot.cogs_state["loaded"])
        
        if len(cogs) == 0 or (len(cogs) == 1 and cogs[0] == "dev" and mode != "reload"):
            return self.t("err", "all_cogs_loaded") if mode == "load" else self.t("err", "all_cogs_unloaded")

        msg_queue = ""
        if mode == "load":
            for cog in cogs:
                try:
                    if input_cogs:
                        await self.bot.change_cogs_state("load", cog)
                    else:
                        await self.bot.load_extension(f"cogs.{cog}")
                    msg_queue += self.t("cmd", "loaded", mcommand_name="load", cog_name=cog)
                except commands.ExtensionAlreadyLoaded:
                    msg_queue += self.t("err", "already_loaded", mcommand_name="load", cog_name=cog)
                except commands.ExtensionNotFound:
                    msg_queue += self.t("err", "not_found", mcommand_name="load", cog_name=cog)
                except commands.ExtensionFailed as e:
                    msg_queue += self.t("err", "failed", mcommand_name="load", cog_name=cog)
                    self.log(40, f"Failed to load cog {cog}!\n{e}")
                except commands.NoEntryPointError:
                    msg_queue += self.t("err", "no_entry_point", mcommand_name="load", cog_name=cog)
                    
        elif mode == "unload":
            for cog in cogs:
                if cog == "dev":
                    if len(cogs) == 1:
                        msg_queue += self.t("cmd", "dev_cog_not_unloaded")
                    continue
                try:
                    if input_cogs:
                        await self.bot.change_cogs_state("unload", cog)
                    else:
                        await self.bot.unload_extension(f"cogs.{cog}")
                    msg_queue += self.t("cmd", "unloaded", mcommand_name="unload", cog_name=cog)
                except commands.ExtensionNotLoaded:
                    msg_queue += self.t("err", "already_unloaded", mcommand_name="unload", cog_name=cog)
                except commands.ExtensionNotFound:
                    msg_queue += self.t("err", "not_found", mcommand_name="unload", cog_name=cog)

        elif mode == "reload":
            for cog in cogs:
                try:
                    await self.bot.reload_extension(f"cogs.{cog}")
                    msg_queue += self.t("cmd", "cog_output", mcommand_name="reload", cog_name=cog)
                except commands.ExtensionNotFound:
                    msg_queue += self.t("err", "extension_not_found", mcommand_name="reload", cog_name=cog)
                except commands.ExtensionNotLoaded:
                    msg_queue += self.t("err", "extension_not_loaded", mcommand_name="reload", cog_name=cog)
                except commands.ExtensionFailed as e:
                    msg_queue += self.t("err", "extension_failed", mcommand_name="reload", cog_name=cog)
                    self.log(40, f"Failed to load cog {cog}!\n{e}")
                except commands.NoEntryPointError:
                    msg_queue += self.t("err", "no_entry_point", mcommand_name="reload", cog_name=cog)

        if mode != "reload" and not input_cogs:
            cogs_copy = cogs.copy()
            for cog in cogs:
                if cog == "dev":
                    continue
                self.bot.cogs_state[adjective].append(cog)
                cogs_copy.remove(cog)
            self.bot.cogs_state[contrary_adjective] = cogs_copy.copy()

        return msg_queue



    @commands.is_owner()
    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["recarregar"])
    async def reload(self, ctx, name: str, sync: Optional[str] = None) -> None:
        
        msg = await self.set_cog("reload", [name])
        await ctx.send(msg)

        if sync in ["sync", "sincronizar"]:
            await ctx.invoke(self.bot.get_command("sync"), guild=None)

    @reload.command(name="translations", aliases=["traduções", "traducoes", "trans"])
    async def reload_trans(self, ctx):
        await self.bot.i18n.reload_translations()
        await ctx.send(self.t("cmd", "translations_output", mcommand_name="reload"))

    @reload.command(name="prefixes", aliases=["prefixos"])
    async def reload_prefixes(self, ctx):
        await self.bot.reload_prefixes()
        await ctx.send(self.t("cmd", "prefixes_output", mcommand_name="reload"))

    @reload.command(name="all", alises=["todos"])
    async def reload_all(self, ctx):
        await ctx.send(await self.set_cog("reload"))
    
    @reload.command(name="everything", aliases=["tudo"])
    async def reload_everything(self, ctx, sync: Optional[str] = None):
        msg_queue = ""

        msg_queue += await self.set_cog("reload")
        
        await self.bot.i18n.reload_translations()
        msg_queue += self.t("cmd", "translations_output", mcommand_name="reload")

        await self.bot.reload_prefixes()
        msg_queue += self.t("cmd", "prefixes_output", mcommand_name="reload")
        
        await ctx.send(msg_queue)

        if sync in ["sync", "sincronizar"]:
            await ctx.invoke(self.bot.get_command("sync"), guild=None)



    @commands.is_owner()
    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["descarregar"])
    async def unload(self, ctx, *, cog_name: str) -> None:
        await ctx.send(await self.set_cog("unload", cog_name.split()))

    @unload.command(name="all")
    async def unload_all(self, ctx) -> None:
        await ctx.send(await self.set_cog("unload"))

    @commands.is_owner()
    @commands.group(case_insensitive=True, invoke_without_command=True, aliases=["carregar"])
    async def load(self, ctx, *, cog_name: str) -> None:
        await ctx.send(await self.set_cog("load", cog_name.split()))

    @load.command(name="all")
    async def load_all(self, ctx) -> None:
        await ctx.send(await self.set_cog("load"))

    @commands.is_owner()
    @commands.hybrid_group(case_insensitive=True, invoke_without_command=True, alises=["sincronizar"])
    async def sync(self, ctx, guild: Optional[int] = None, copy: Optional[bool] = True) -> None:
        async with ctx.typing():
            if not guild: guild = ctx.guild.id
            guild_obj = discord.Object(guild)
            try:
                if copy:
                    self.bot.tree.copy_global_to(guild=guild_obj)
                await self.bot.tree.sync(guild=guild_obj)
            except app_commands.CommandSyncFailure:
                #TODO Translate
                await ctx.send(self.t("err", "command_sync_failure"))

        await ctx.send(self.t("cmd", "output", guild=ctx.guild))

    @commands.is_owner()
    @sync.command(name=_T("global"))
    async def sync_global(self, ctx) -> None:
        async with ctx.typing():
            try:
                await self.bot.tree.sync()
            except app_commands.CommandSyncFailure:
                await ctx.send(self.t("err", "command_sync_failure", mcommand_name="sync"))
        await ctx.send(self.t("cmd", "output"))
        
    @commands.is_owner()
    @commands.hybrid_command()
    #@app_commands.describe(cog_name=_T("cog_name"))
    async def cog(self, ctx, cog_name: str) -> None:
        """Check for one single cog."""
        try:
            await self.bot.load_extension(f"cogs.{cog_name}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(self.t("cmd", "is_loaded_output", cog_name=cog_name))
        except commands.ExtensionNotFound:
            await ctx.send(self.t("err", "not_found_output", cog_name=cog_name))
        else:
            await ctx.send(self.t("cmd", "is_unloaded_output", cog_name=cog_name))
            await self.bot.unload_extension(f"cogs.{cog_name}")

    @commands.is_owner()
    @commands.hybrid_command()
    async def cogs(self, ctx) -> None:
        """Checks all cogs."""
        loaded = self.bot.cogs_state["loaded"]
        unloaded = self.bot.cogs_state["unloaded"]
        client = self.bot.user
        embed = discord.Embed(title="Cogs")
        embed.add_field(name=self.t("embed_fields", "loaded"), value=", ".join(loaded))
        embed.add_field(name=self.t("embed_fields", "unloaded"), value=", ".join(unloaded) if unloaded else "N/A")
        embed.set_author(name=client, icon_url=client.avatar)
        embed.set_footer(text=f"ID: {client.id}")

        await ctx.send(embed=embed)


    #DANGEROUS
    @commands.is_owner()
    @commands.hybrid_command(name=_T("print"))
    #@app_commands.describe(thing=_T("print"))
    async def _print(self, ctx, thing):
        """Prints a value from the bot"""
        try:
            await ctx.send(eval(thing))
        except Exception as err:
            self.log(40, err)
            await ctx.send(self.t("err", "exception", error=err))


    #DANGEROUS
    @commands.is_owner()
    @commands.hybrid_command(alises=["reboot", "reiniciar"])
    async def restart(self, ctx):
        await ctx.send(self.t("cmd", "output"))
        os.execv(sys.executable, ['python3'] + sys.argv)


    @commands.is_owner()
    @commands.command()
    async def sudo(self, ctx, channel: Optional[discord.TextChannel], member: discord.Member | discord.User, *, command: str):
        """Run a command as another user optionally in another channel."""
        msg = ctx.message
        new_channel = channel or ctx.channel
        msg.channel = new_channel
        msg.author = member
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)



    #loader and unloader
    async def cog_load(self) -> None:
        print("Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        print("Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot):
    await bot.add_cog(Dev(bot))

async def teardown(bot):
    await bot.remove_cog("Dev")
