#!/bin/sh

sudo rm -fv '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/*'

#sudo find '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support' -type d -name '*phoenix*' -exec rm -rfv {} \;

sudo find '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins' -type d -iname '*phoenix*' -exec rm -rfv {} \;

cp -prv SageTVPhoenix.bundle /var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/

sudo service plexmediaserver stop
sleep 1
sudo service plexmediaserver start
