#!/usr/bin/env bash

echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "Done!"

echo "Installing config files..."
mv example_appsettings.yaml appsettings.yaml
touch prefixes.json
echo "Done!"
