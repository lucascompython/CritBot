# CritBot (the discord bot)<img src="https://cdn.discordapp.com/attachments/628637327878520872/1017256259138900030/unknown.png" width="3.5%" heigth="3.5%"/>

This is a discord bot written in rust with serenity and poise.
The bot has a custom [i18n](src/i18n/) system.

## Features

+ Translations - For now only English and Portuguese

## Installation & Execution

This bot was only tested on Linux.
The installation steps are as follows:

I have only tested PostgreSQL >=15.2 but it should work with other versions.

Create a database and a user with the `psql` tool:

```pgsql
CREATE ROLE user WITH LOGIN PASSWORD 'yourpw';
CREATE DATABASE crit OWNER user;
```

## Todo's (mostly by order)

+ [X] add i18n system
+ [ ] add i18n to app_commands and on commands descriptions
+ [ ] add Music


## Rewrite Notes

+ The new i18n system is stateless, meaning that in contrast to the old one, I'm not doing any hacky stuff to get determine the locale before a command is executed. Now the locale is determined every time a translation is needed.
