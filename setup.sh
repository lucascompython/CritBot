#!/usr/bin/env bash

echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "Done!"


echo "Downloading Lavalink..."
wget "https://github.com/freyacodes/Lavalink/releases/download/3.6.2/Lavalink.jar" -O ./config/Lavalink.jar
echo "Done!"

echo "Installing config files..."
mv ./config/example_appsettings.yaml ./config/appsettings.yaml
mv ./config/example_application.yml ./config/application.yml
echo "{}" > prefixes.json
echo "{}" > ./i18n/langs.json
echo "Done!"
