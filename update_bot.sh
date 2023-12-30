#!/bin/bash

# This script is used to update the bot from the git repository


if [ "$PWD" != "/home/$USER/critbot" ]; then
    cd /home/$USER/critbot
fi


export PATH=/home/$USER/.local/bin:$PATH # for pdm

git pull

tmux kill-session -t critbot

tmux new-session -d -s critbot "source .venv/bin/activate && pdm start -l 0.0.0.0:2333"