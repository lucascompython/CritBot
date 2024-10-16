#!/usr/bin/env bash

echo "To install dependencies, run 'uv sync'"

echo "Downloading Lavalink..."
wget "https://github.com/freyacodes/Lavalink/releases/download/4.0.8/Lavalink.jar" -O ./config/Lavalink.jar
echo "Done!"

echo "Installing config files..."
cp ./config/appsettings.example.yaml ./config/appsettings.yaml
cp ./config/application.example.yml ./config/application.yml
mkdir logs
echo "{}" > ./logs/bug_reports.json # TODO: Make this in the database
echo "Done!"
echo "Don't forget to edit the config files! (config/appsettings.yaml, config/application.yml)"
echo "And don't forget to install PostgreSQL if you don't already have it!"
