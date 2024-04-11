#!/bin/bash
date=$(date -u +"%Y%d%m%H%M")
source venv/bin/activate
pyinstaller --name="shellar" --onefile --windowed --hidden-import=requests --hidden-import=markdown --hidden-import=tkhtmlview  --distpath="~/build/shellar.io.v$date/dist" --icon="../graSSHopper/icons/shellar.icns" main.py