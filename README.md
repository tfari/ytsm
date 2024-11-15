# ytsm
***YTSM*** is a YT Subscription Manager. Add, remove, and update any channels you want to follow; watch and keep a
log of the videos you have watched. ***YTSM*** uses YT's RSS feeds, which return information of the newest 15 videos of
a Channel, to maintain a local database of videos by saving the last 100 videos for each Channel. The video 
information can be updated by channel or all at the same time. You can also get real-time notifications on updates by
using the command **notify-update**, which calls an update on all Channels and then utilizes the "notify-send" 
(https://vaskovsky.net/notify-send/) tool to message the system's notification tray. You can schedule the call of this 
command via something like cron, and even mute any Channels if you don't want to receive notifications for them.

***YTSM*** provides cli, tui, and gui frontends to access, filter, search, and well watch the videos in your default browser. 
The three interfaces can be configured via the settings.json file in the data folder, or via the Settings pane on the GUI.

The format for searching videos by date is "YYYY-MM-DD YYYY-MM-DD", where the first date is the lower range and the second date 
the upper range.

## Graphical User Interface
![](https://github.com/tfari/ytsm/blob/main/images/gui-1.png)

`python ytsm.py gui`

The GUI provides two main ways of browsing the data: by Channel and by Videos, each providing their own set of filters
and search functions.

The GUI is implemented in tk, which means it may not look the same in all platforms. However, the colors, fonts, and 
sizes can be configured via the Settings tab.

## Text User Interface
![](https://github.com/tfari/ytsm/blob/main/images/tui-gif.gif)

`python ytsm.py tui`

The TUI is implemented in urwid, which means it is not available for Windows. It provides two main ways of browsing the
data: by Channel and by Videos, each providing their own set of filters and search functions.

You can configure the colors and command keys via the settings.json file.
![](https://github.com/tfari/ytsm/blob/main/images/tui-help.png)

## Command-line usage
```
Whenever NAME is used, you can enter either the full name, or a portion of it, the program will find the appropiate 
Channel/Video and prompt you for confirmation if there is more than one option.

* factory-restore [--all| --setts | --db | --help]
    Restore the data for the application to factory, either everything, or only the settings and/or db.
* notify-update
    Update all channels and notify about the (non-muted) changed ones. For usage with crontab or other scheduling of 
    commands. 
    This implementation uses the "notify-send" tool to access the system's notification tray.
    More info on: https://vaskovsky.net/notify-send/
* channels [--new/-n | --unwatched/-u]
    List all channels. If -n is passed show only channels with new videos, if -u is passed show only channels with 
    unwatched videos. 
* add URL 
    Add a channel via a yt url. Accepted URL types: "/channel", "/user", "/c", "/watch", "/@"
* remove NAME
    Remove a channel by its name.
* update NAME [-a]
    Update a channel, or all channels if -a is passed.
* visit NAME
    Visit a Channel's YT page.
* mute NAME
    Mute a Channel's notifications
* unmute NAME
    Unmute a Channel's notifications
* find TERM [--videos/-v | --description | --date | --channel-name]
    Find channels by name. If -v is passed, find videos by name, if -d is passed, it finds videos by description, 
    if --date is passed, find videos by date range. If --channel-name is passed, only search within a specific channel.
    --date takes two dates in the form YYYY-MM-DD to search in between.
* videos TERM [CHANNEL_NAME] [--new/-n | --unwatched/-u | --limit/-l INT | --no-limit/-nl]
    List the last 15 videos of CHANNEL_NAME (if not passed, it lists the last 15 videos of all channels).
    Using --new/-n or --unwatched/-u you can filter the videos to only new or unwatched respectively.
    You can set the amount of videos to show using --limit/-l, or use --no-limit/-nl to show all videos.
* detail NAME
    Show the details of a video (name, channel, publication date, description).
* watch NAME
    Open a video in your web browser, and mark it as watched.
* watched NAME [-c]
    Mark a video as watched, or all videos in a channel if -c is passed
* tui
    Open the textual user interface (not for Windows).
* gui
    Open the graphical user interface.
```

## Requirements
### Python requirements
* python 3.9+ (due to type hinting)
* requests
* beautifulsoup4
* click
* pillow
* colorama (windows ansi cli coloring)
* urwid (for the tui, not available on Windows)
* lxml (for the XML parser)

### Extra
* notify-update (For usage of ***YTSM*** with chron or other task scheduling. It allows to use the system's 
  notification tray for notifying when there are new Videos)
  * https://vaskovsky.net/notify-send/
  * https://vaskovsky.net/notify-send/linux.html


## Known bugs
_NOTICE_: ***YTSM*** uses YT's rss feed endpoint, which is known to be down from time to time, so it is possible to 
experience temporal 404 errors when attempting to update channels.

* Channel thumbnail URLs sometimes point to wrong images for a while.
* European IPs cannot add channels using channel-type URLs, only via video URLs.

### For GUI on fedora
On error: 
```
X Error of failed request:  BadLength (poly request too large or internal Xlib length error)
  Major opcode of failed request:  139 (RENDER)
  Minor opcode of failed request:  20 (RenderAddGlyphs)
  Serial number of failed request:  302
  Current serial number in output stream:  323
```
Try:
`sudo dnf remove google-noto-emoji-color-fonts`
