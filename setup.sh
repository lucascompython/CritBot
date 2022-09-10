#!/usr/bin/env bash

echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "Done!"

echo "Installing config files..."
mv ./config/example_appsettings.yaml ./config/appsettings.yaml
echo "{}" > prefixes.json
echo "{}" > ./i18n/langs.json
echo "Done!"
