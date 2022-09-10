#/usr/bin/env python3

import os
import json
import argparse


class SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"

def create_dump(contents: dict) -> dict:
    dump = {}
    for key, val in contents.items():
        for k, v in val.items():

            if key not in dump:
                dump[key] = {k: {q: "" for q in v.keys()}}

            if k not in dump[key]:
                dump[key][k] = {q: "" for q in v.keys()}
    
            else:
                dump[key][k] = {q: "" for q in v.keys()}
    return dump

cog_template = """from discord.ext import commands

class {cog_name}(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.t = self.bot.i18n.t
        self.log = self.bot.logger.log
        



        
    async def cog_load(self) -> None:
        self.log(20, "Loaded {name} cog!".format(name=self.__class__.__name__))
        
    async def cog_unload(self) -> None:
        self.log(20, "Unloaded {name} cog!".format(name=self.__class__.__name__))
        

async def setup(bot) -> None:
    await bot.add_cog({cog_name}(bot))
    
async def teardown(bot) -> None:
    await bot.remove_cog("{cog_name}")"""






def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", help="This command has 2 possible modes: (add) cog and (add) translation. Add cog will add a cog file with a template and add translate will add a translation file. All input should be added without file extensions.", nargs=2, type=str, required=False)
    parser.add_argument("-c", "--copy", help="This command will copy the keys of one translation file to another. Example: -c en.misc es.misc. Can also copy all the keys. Example: -c en.* es.*. File names may need to be inside of quotes when copying all the keys. All input should be added without file extensions.", nargs=2, type=str, required=False)
    return parser.parse_args()

def main() -> None:
    args = get_args()
    add = args.add
    copy = args.copy
    if add:
        mode = add[0].lower()
        name = add[1].lower()
        if mode in ["cog", "ext", "extension", "c"]:

            path = f"./cogs/{name}.py"
            if not os.path.isfile(path):
                with open(path, "w") as f:
                    f.write(cog_template.format_map(SafeDict(cog_name=name.capitalize())))
                print(f"Created {path}.py")
            else:
                print(f"{path} already exists!")

        elif mode in ["trans", "translation", "t"]:
            path = f"./config/translations/{name}.json"

            if os.path.isfile(path): return print(f"{path} already exists!")

            with open(path, "w") as f:
                f.write("{}")
            print(f"Created {path}!")

    elif copy:
    
        original = copy[0].lower()
        new = copy[1].lower()
        if original.split(".")[1] == "*" and new.split(".")[1] == "*":
            original = original.split(".")[0]
            new = new.split(".")[0]
            path = "./config/translations"
            for file in os.listdir(path):
                if file.startswith(original):
                    with open(path + "/" + file, "r") as f:
                        contents = json.load(f)

                    
                    dump = create_dump(contents)

                    with open(path + "/" + file.replace(original, new), "w") as f:
                        json.dump(dump, f, indent=4)
                
                elif file.startswith(new):
                    continue

            return print(f"Succesfully created {new} translations from {original} translations!")

        path_original = f"./config/translations/{original}.json"
        path_new = f"./config/translations/{new}.json"

        if os.path.isfile(path_new): return print(f"{path_new} already exists!")

        with open(path_original, "r") as f:
            contents = json.load(f)

        dump = create_dump(contents)
                


        with open(path_new, "w") as f:
            json.dump(dump, f, indent=4)

                    #print(v)
                    #dump[key] = {l: "" for l in v.keys()}

                #dump[key] = {k: "" for k in val.keys()}

        print(f"Created {path_new} with the keys of {path_original}!")



if __name__ == "__main__":
    main()
