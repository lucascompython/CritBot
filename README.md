# CritBot (the discord bot)<img src="https://cdn.discordapp.com/attachments/628637327878520872/1017256259138900030/unknown.png" width="3.5%" heigth="3.5%">

This is discord bot written in discord.py v2.0 that aims at exploring the possibilities of a discord bot.<br>Right now the bot is quite simple and most of the code aims at extensibility.<br>The bot has a custom implementation of i18n.<br>You can invite the bot [here](https://discord.com/api/oauth2/authorize?client_id=832679098740506644&permissions=8&scope=bot).

## Installation & Execution
I would prefer if you don't run an instance of my bot. You can just invite him [here](https://discord.com/api/oauth2/authorize?client_id=832679098740506644&permissions=8&scope=bot).<br>
Nevertheless, the installation steps are as follows:<br>
This bot was only teted on linux. 
```bash
git clone https:/github.com/lucascompython/CritBot.git
cd CritBot
./setup.sh
#change the appsettings.yaml file with your token and information
python3 main.py
```


## Todo's (mostly by order)
- [X] add internationalization with i18n
- [X] add i18n to app_commands and on commands descriptions
- [ ] get a real database probably PostgreSql
- [ ] add Music
- [ ] Cythonize i18n custom module
- [ ] add most of the Discord API


## Known "bugs"
- The interaction name and description is is set per user locale while everything else is set per guild language.

## Contributions
Feel free to help.<br>
If you have any questions on the code you can send me a DM on my Discord (Lucas cheio da drip#0230)

# License
This project is licensed under the GPL3 license.