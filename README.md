# CritBot (the discord bot)<img src="https://cdn.discordapp.com/attachments/628637327878520872/1017256259138900030/unknown.png" width="3.5%" heigth="3.5%"/>

This is discord bot written with discord.py v2.0 that aims at exploring the possibilities of a discord bot.  
Right now the bot is quite simple and most of the code aims at extensibility.  
The bot has a custom implementation of [i18n](i18n/).  
The only supported languages for now are Portuguese and English.  
Shoutout to the team behind <https://returnyoutubedislike.com> for being awesome.

## Installation & Execution

This bot was only tested on Linux.  
Python 3.10+ is required.  
You can invite him [here](https://discord.com/api/oauth2/authorize?client_id=931322447117053972&permissions=8&scope=bot).  
The installation steps are as follows:

I have only tested PostgreSQL 15.2 but it should work with other versions.

Create a database and a user with the `psql` tool:

```pgsql
CREATE ROLE user WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE crit OWNER user;
```

And then

```bash
git clone https://github.com/lucascompython/CritBot.git
cd CritBot
# install PDM (build tool)
pip install pdm # Also, fuck PEP 668

# activate virtual environmet
eval $(pdm venv activate)

# install dependencies
pdm install

pdm run setup
pdm run start --help

#change the appsettings.yaml file with your token and information
```

## Todo's (mostly by order)

- [X] add internationalization with i18n
- [X] add i18n to app_commands and on commands descriptions
- [X] add Music
- [X] get a real database probably PostgreSql
- [ ] update to wavelink 2.0
- [ ] follow ruff's and mypy's suggestions
- [ ] add support for other languages with Google Translate
- [ ] add Docker support

## Known "bugs"

- URGENT - Probably on commands that take more time to execute, if another command is invoked while the other is executing the translations might get mixed up. Probably will need to inplement a sort of message queue linked to a guild's channel.  
- The interaction name, description, choices, etc. are set per user locale while everything else is set per guild language.
- The helper.py file is a mess and probably has some bugs.

## Contributions

Feel free to help.  
If you have any questions on the code you can send me a DM on my Discord (Lucas cheio da drip#0230)  
I recommend using [PDM](https://pdm.fming.dev/) as the build tool. [Ruff](https://beta.ruff.rs/docs/) as a linter and [Mypy](https://mypy.readthedocs.io/en/stable/) as a type checker.

# License

This project is licensed under the GPL3 license.
