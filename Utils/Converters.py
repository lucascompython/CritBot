from discord.ext import commands


class BoolConverter(commands.Converter):
    @classmethod
    async def convert(cls, ctx, argument: str):
        if argument.lower() in (
            "yes",
            "y",
            "true",
            "t",
            "1",
            "on",
            "enable",
            "enabled",
            "sim",
            "s",
            "verdadeiro",
            "v",
            "ligado",
            "ativado",
        ):
            return True
        elif argument.lower() in (
            "no",
            "n",
            "false",
            "f",
            "0",
            "off",
            "disable",
            "disabled",
            "nao",
            "não",
            "n",
            "falso",
            "f",
            "desligado",
            "desativado",
        ):
            return False
        else:
            raise commands.BadArgument("Invalid boolean value.")
