# Phoenix Channel Plugin for Plex

This Plex Plugin adds a SageTV/Phoenix Plugin to the Plex Channels.

The Channel enables you to view your existing SageTV content using the logical views that Phoenix has exposed, such as
showing only the unwatched tv shows grouped by show, etc.

Since it uses Phoenix Views, you can view other "non media" items such as your current recording schedule.

The API of a Plex Channel is really limiting, so, it will not enable you to schedule recordings, cancel recordings, delete media, etc.

# Installation
Download the latest release from the releases area

Extract it and copy the SageTVPhoenix.bundle folder to the Library/Application Support/Plex Media Server/Plug-ins/ folder

Restart Plex Media Server

You should see a new channel for Phoenix.  You will want to launch the channel, and then use the Preferences for that plugin to set the sagetv server, port, username and password.  IF your plex server is running on the same server as your SageTV server, then use 'localhost' for the server.

# Requirements
Latest Phoenix Core plugin
Latest Sagex APIs plugin (may need to manually download and install this from https://github.com/stuckless/sagetv-sagex-api/releases) (at least version 7.1.9.23)

# Gallery
https://plus.google.com/photos/101598841452026913121/albums/5970615206594113041
