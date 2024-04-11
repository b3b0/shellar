#!/bin/bash

ORIGINAL_ICON="shellar.png"
ICONSET_FOLDER="shellar.iconset"
mkdir -p $ICONSET_FOLDER

sips -Z 16  $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_16x16.png
sips -Z 32  $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_32x32.png
sips -Z 64  $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_64x64.png
sips -Z 128 $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_128x128.png
sips -Z 256 $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_256x256.png
sips -Z 512 $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_512x512.png

sips -Z 32  $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_16x16@2x.png
sips -Z 64  $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_32x32@2x.png
sips -Z 256 $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_128x128@2x.png
sips -Z 512 $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_256x256@2x.png
sips -Z 1024 $ORIGINAL_ICON --out $ICONSET_FOLDER/icon_512x512@2x.png

iconutil -c icns $ICONSET_FOLDER

rm -r $ICONSET_FOLDER