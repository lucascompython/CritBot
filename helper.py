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
            lang = name.split()[0]
            path = f"./config/translations/{lang}/{name[3:]}.json"

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
            path = "./config/translations/" + original
            new_path = "./config/translations/" + new

            if not os.path.isdir(new_path):
                os.mkdir(new_path)
                print(f"Created {new_path}!")

            for file in os.listdir(path):
                if os.path.isfile(os.path.join(new_path, file)):
                    print(f"{new_path}/{file} already exists, skipping!")
                    continue

                with open(path + "/" + file, "r") as f:
                    contents = json.load(f)

                dump = create_dump(contents)
            

                with open((path + "/" + file).replace(original, new), "w") as f:
                    json.dump(dump, f, indent=4)
            

            return print(f"Succesfully created {new} translations from {original} translations!")

        original_lang = original.split(".")[0]
        new_lang = new.split(".")[0]

        original_path = f"./config/translations/{original_lang}"
        new_path = f"./config/translations/{new_lang}"

        original_file_path = os.path.join(original_path, original[3:] + ".json")
        new_file_path = os.path.join(new_path, new[3:] + ".json")

        if not os.path.isdir(new_path):
            os.mkdir(new_path)
            print(f"Created {new_path}!")

        if os.path.isfile(new_file_path): return print(f"{new_file_path} already exists!")


        with open(original_file_path, "r") as f:
            contents = json.load(f)

        dump = create_dump(contents)
                


        with open(new_file_path, "w") as f:
            json.dump(dump, f, indent=4)

        print(f"Created {new_path} with the keys of {original_path}!")



if __name__ == "__main__":
    main()
