#!/usr/bin/env bash

echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "Done!"

echo "Installing config files..."
mv example_appsettings.yaml appsettings.yaml
echo "{}" > prefixes.json
echo "Done!"
