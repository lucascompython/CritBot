# CritBot (the discord bot)<img src="https://cdn.discordapp.com/attachments/628637327878520872/1017256259138900030/unknown.png" width="3.5%" heigth="3.5%"/>

This is a discord bot written with discord.py v2.0.  
The bot has a custom [i18n](i18n/) system.  
The only translated languages for now are Portuguese and English.  

# Rewrite!
Since Wavelink is now archived, I decided I might as well rewrite the whole thing!  
This project is currently being rewritten [here](https://github.com/lucascompython/CritBot/tree/rust-rewrite).

## Features

+ Translations - For now only English and Portuguese
+ High quality audio
+ Youtube's Dislikes - <https://returnyoutubedislike.com>
+ [Sponsorblock](https://sponsor.ajay.app/) - <https://github.com/topi314/Sponsorblock-Plugin>
+ Music AutoPlay - When enabled the bot will play music based on the music played that session
+ Downloading Music - Download anything (get's converted to mp3) that [yt-dlp](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) supports, at 320kbps. Discord limits files bigger than 25MB (around, 11min.)
+ Audio Filters - Nightcore, 8d, reverb, etc.
+ Multiple Platform Support - Youtube, YT Music, Spotify, Apple Music, Twitch, Sondcloud, Vimeo and Bandcamp
+ Reddit memes
+ Both prefixed and slash commands

## Installation & Execution

This bot was only tested on Linux.  
Python 3.13+ is required.  
You can invite it [here](https://discord.com/oauth2/authorize?client_id=888100964534456361&permissions=8&integration_type=0&scope=bot).  
The installation steps are as follows:

I have only tested PostgreSQL >=15.2 but it should work with other versions.

Create a database and a user with the `psql` tool:

```pgsql
CREATE ROLE user WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE crit OWNER user;
```

And then

```bash
git clone https://github.com/lucascompython/CritBot.git
cd CritBot
# install uv https://github.com/astral-sh/uv (build tool)

# activate virtual environmet
source ./venv/bin/activate

# install dependencies
uv pip install

./setup.sh
java -jar .config/Lavalink.jar

# change the appsettings.yaml file with your token and information
python3 launcher.py -l 0.0.0.0:2333

```

## Todo's (mostly by order)

+ [X] add internationalization
+ [X] add i18n to app_commands and on commands descriptions
+ [X] add Music
+ [X] get a real database probably PostgreSql
+ [X] update to wavelink 3
+ [ ] remake the i18n system
+ [ ] update help menu on specific command
+ [ ] add support for other languages with Google Translate
+ [ ] add Docker support

## Known "bugs"

+ If two translations are being processed at the same time, it might error. I know this is stupid.
+ The interaction name, description, choices, etc. are set per user locale while everything else is set per guild language.

## Contributions

Feel free to help.  
If you have any questions on the code you can send me a DM on my Discord (lucas_delinhares)  

## License

This project is licensed under the GPL3 license.
