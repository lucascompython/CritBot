import os
import argparse
#from collections import defaultdict


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


file_template = """from discord.ext import commands

class {cog_name}(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        



        
    async def cog_load(self) -> None:
        self.bot.logger.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        self.bot.logger.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog({cog_name}(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("{cog_name}")"""




def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", help="Add an extension file with a cog inside. Input the name of the file without extension", metavar="N", type=str)
    return parser.parse_args()

def main() -> None:
    args = get_args()
    path = f"./cogs/{args.add}.py"
    if not os.path.isfile(path):
        with open(path, "w") as f:
            f.write(file_template.format_map(SafeDict(cog_name=args.add.capitalize())))
        print(f"Created {args.add}.py")
    else:
        print(f"{args.add} already exists!")


if __name__ == "__main__":
    main()
