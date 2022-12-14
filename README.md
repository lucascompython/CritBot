# CritBot (the discord bot)<img src="https://cdn.discordapp.com/attachments/628637327878520872/1017256259138900030/unknown.png" width="3.5%" heigth="3.5%"/>

This is discord bot written with discord.py v2.0 that aims at exploring the possibilities of a discord bot.  
Right now the bot is quite simple and most of the code aims at extensibility.  
The bot has a custom implementation of [i18n](i18n/).  
The only supported languages for now are Portuguese and English.  
Shoutout to the team behind <https://returnyoutubedislike.com> for making their API public.

## Installation & Execution

This bot was only tested on Linux.  
Python ^3.10 is required.  
I would prefer if you don't run an instance of my bot. <!---You can just invite him [here](https://discord.com/api/oauth2/authorize?client_id=832679098740506644&permissions=8&scope=bot).-->  
Nevertheless, the installation steps are as follows:

```bash
git clone https:/github.com/lucascompython/CritBot.git
cd CritBot
./setup.sh
#change the appsettings.yaml file with your token and information
./launcher.py --help
```

## Todo's (mostly by order)

- [X] add internationalization with i18n
- [X] add i18n to app_commands and on commands descriptions
- [ ] add Music
- [ ] get a real database probably PostgreSql
- [ ] add support for other languages with Google Translate
- [ ] add Docker support
- [ ] add most of the Discord API

## Known "bugs"

- URGENT - Probably on commands that more time to execute, if another command is invoked while the other is executing the translations might get mixed up. Probably will need to inplement a sort of message queue linked to a guild's channel.  
- The interaction name, description, choices, etc. are set per user locale while everything else is set per guild language.

## Contributions

Feel free to help.  
If you have any questions on the code you can send me a DM on my Discord (Lucas cheio da drip#0230)

# License

This project is licensed under the GPL3 license.
