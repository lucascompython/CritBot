from discord.ext.commands import Converter


class BoolConverter(Converter):
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
            raise ValueError("Invalid boolean argument")
