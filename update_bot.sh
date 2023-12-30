#!/bin/bash

# This script is used to update the bot from the git repository and start the bot.
# This is used by the systemd service.
# And the cronjob will use the systemd service to restart the bot at 02 AM.



# check if it is for lavalink
if [ "$1" == "lavalink" ]; then

    if [ "$PWD" != "$HOME/critbot/config" ]; then
        cd $HOME/critbot/config
    fi

    if tmux has-session -t lavalink 2>/dev/null; then
        tmux kill-session -t lavalink
    fi

    echo "Starting lavalink" > log.txt
    tmux new-session -d -s lavalink "$USER/.sdkman/candidates/java/current/bin/java -jar Lavalink.jar" # using sdkman
    exit 0
fi


if [ "$PWD" != "$HOME/critbot" ]; then
    cd $HOME/critbot
fi


export PATH=/home/$USER/.local/bin:$PATH # for pdm

git pull

if tmux has-session -t critbot 2>/dev/null; then
    tmux kill-session -t critbot
fi

tmux new-session -d -s critbot "source .venv/bin/activate && pdm start -l 0.0.0.0:2333"

# crontab -e
# 0 2 * * * /usr/bin/systemctl --user restart critbot.service
