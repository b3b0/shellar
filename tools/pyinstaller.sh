#!/bin/bash
date=$(date -u +"%Y%d%m%H%M")
pyinstaller --name="shellar.io" --onefile --windowed --distpath="~/build/shellar.io.v$date/dist" --icon="../graSSHopper/icons/shellar.icns" main.py