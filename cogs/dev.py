import discord
from discord.ext import commands

import os, sys

class Dev(commands.Cog):
    """Classe que define comandos que apenas o desenvolvedor pode usar."""
    def __init__(self, bot) -> None:
        self.bot = bot


    async def cog_all(self, mode: str) -> str:
        """Loads or unloads (except dev cog) all cogs."""
        adjective = mode + "ed"
        contrary = lambda adj: "load" if adj == "unload" else "unload"
        contrary_adjective = contrary(mode) + "ed"

        cogs = self.bot.cogs_state[contrary_adjective]
        cogs_copy = cogs.copy()
        
        if len(cogs) != 0:
            msg_queue = ""
            for cog in cogs:
                if mode == "load":
                    await self.bot.load_extension(f"cogs.{cog}")
                    msg_queue += f"**{cog}** foi carregado com sucesso!\n"
                elif mode == "unload":
                    if cog == "dev":
                        continue
                    await self.bot.unload_extension(f"cogs.{cog}")
                    msg_queue += f"**{cog}** foi descarregado com sucesso!\n"
            
            for cog in cogs:
                if cog == "dev":
                    continue
                self.bot.cogs_state[adjective].append(cog)
                cogs_copy.remove(cog)
            self.bot.cogs_state[contrary_adjective] = cogs_copy

            return msg_queue
        return "Todos os cogs disponiveis já foram carregados!"



    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx, cog_name: str, sincronizar: str | None = None) -> None:
        try:
            await self.bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send(f"**{cog_name}** foi recarregado.")
        except:
            return await ctx.send(f"**{cog_name}** não existe ou não foi carregado...")

        if sincronizar in ["sync", "sincronizar"]:
            await ctx.invoke(self.bot.get_command("sync"), guild=None)

    @commands.is_owner()
    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def unload(self, ctx, *, cog_name: str) -> None:
        cog_name = cog_name.split()
        msg_queue = ""
        for cog in cog_name:
            if cog == "dev":
                msg_queue += "Não podes dar unload a **dev**.\n"
                continue
            try:
                await self.bot.change_cogs_state("unload", cog)
                msg_queue += f"**{cog}** foi descarregado.\n"
            except commands.ExtensionNotLoaded:
                exts = [i.replace("cogs.", "") for i in self.bot.initial_extensions]
                if cog in exts:
                    msg_queue += f"**{cog}** já está descarregado.\n" 
                else:
                    msg_queue += f"**{cog}** não pôde ser descarregada (prob. não existe).\n"

        await ctx.send(msg_queue)


    @unload.command(name="all")
    async def unload_all(self, ctx) -> None:

        msg = await self.cog_all("unload")
        await ctx.send(msg)


    @commands.is_owner()
    @commands.group(case_insensitive=True, invoke_without_command=True)
    async def load(self, ctx, *, cog_name: str) -> None:
        cog_name = cog_name.split()
        msg_queue = ""
        
        for cog in cog_name:
            try:
                await self.bot.change_cogs_state("load", cog)
                msg_queue += f"**{cog}** foi carregado.\n"
            except commands.ExtensionAlreadyLoaded:
                msg_queue += f"**{cog}** já está carregado.\n"
            except commands.ExtensionNotFound:
                msg_queue += f"**{cog}** não pôde carregada (prob. não existe).\n"
            except commands.ExtensionFailed:
                msg_queue += f"**{cog}** não foi carregada pois falhou a inicializar.\n"
        await ctx.send(msg_queue)

    @load.command(name="all")
    async def load_all(self, ctx) -> None:

        msg = await self.cog_all("load")
        await ctx.send(msg)


    @commands.is_owner()
    @commands.hybrid_group()
    async def sync(self, ctx, guild: int | None) -> None:
        async with ctx.typing():
            if not guild: guild = ctx.guild.id
            guild_obj = discord.Object(guild)
            self.bot.tree.copy_global_to(guild=guild_obj)
            await self.bot.tree.sync(guild=guild_obj)
        await ctx.send(f"**{ctx.guild}** foi sincronizado com o bot.")

    @commands.is_owner()
    @sync.command(name="global")
    async def _global(self, ctx) -> None:
        async with ctx.typing():
            await self.bot.tree.sync()
        await ctx.send("O bot foi sincronizado globalmente.")
        
    @commands.is_owner()
    @commands.hybrid_command()
    async def cog(self, ctx, cog_name: str | None = None) -> None:
        """Check for one single cog."""
        try:
            await self.bot.load_extension(f"cogs.{cog_name}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"**{cog_name}** está carregado.")
        except commands.ExtensionNotFound:
            await ctx.send(f"**{cog_name}** não encontrado.")
        else:
            await ctx.send(f"**{cog_name}** não está carregado.")
            await self.bot.unload_extension(f"cogs.{cog_name}")

    @commands.is_owner()
    @commands.hybrid_command()
    async def cogs(self, ctx) -> None:
        """Checks all cogs."""
        loaded = self.bot.cogs_state["loaded"]
        unloaded = self.bot.cogs_state["unloaded"]
        client = self.bot.user
        embed = discord.Embed(title="Cogs")
        embed.add_field(name="Carregados", value=", ".join(loaded))
        embed.add_field(name="Descarregados", value=", ".join(unloaded) if unloaded else "N/A")
        embed.set_author(name=client, icon_url=client.avatar)
        embed.set_footer(text=f"ID: {client.id}")

        await ctx.send(embed=embed)


    #DANGEROUS
    @commands.is_owner()
    @commands.hybrid_command(name="print")
    async def _print(self, ctx, thing):
        try:
            await ctx.send(eval(thing))
        except Exception as err:
            await ctx.send(f"Algo deu merda: {err}")


    #DANGEROUS
    @commands.is_owner()
    @commands.hybrid_command(alises=["reboot"])
    async def restart(self, ctx):
        await ctx.send("Reiniciando!")
        os.execv(sys.executable, ['python3'] + sys.argv)

    @commands.is_owner()
    @commands.hybrid_command()
    async def reload_prefixes(self, ctx):
        await self.bot.reload_prefixes()
        await ctx.send("Prefixos recarregados.")
                    
    @commands.is_owner()
    @commands.hybrid_command(name="reload_translations")
    async def _reload_translations(self, ctx):
        await self.bot.i18n.reload_translations()
        await ctx.send("Traduções recarregadas.")

    #error handling

    #    @reload.error
    #    async def reload_error(ctx, error):
    #        if isinstance(error, commands.CommandInvokeError):
    #            await ctx.send("Esse cog")



    #loader and unloader
    async def cog_load(self) -> None:
        self.bot.logger.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))

    async def cog_unload(self) -> None:
        self.bot.logger.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))


async def setup(bot):
    await bot.add_cog(Dev(bot))

async def teardown(bot):
    await bot.remove_cog("Dev")
