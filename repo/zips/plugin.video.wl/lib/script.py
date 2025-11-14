import sys
import xbmcgui
import xbmcaddon
from utils import list_json_lists, restore

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')


def infotext():
    txt = """Um ein Widget von MyWatchlist bei Änderungen des Listeninhalts zu aktualisieren, muss in dem Pfad \n&t=$INFO\[Window(10000).Property(NAME_OF_JSON.time)]\neingetragen werden.
    \nBeispiel: Pfad -> plugin://plugin.video.wl/?action=show&json=watchlist \nwird zu \nplugin://plugin.video.wl/?action=show&json=watchlist&t=$INFO\[Window(10000).Property(watchlist.time)].
    \nDie \ nach INFO weglassen.
    \nTo update a MyWatchlist widget when the list content changes, the following must be entered in the path: \n&t=$INFO\[Window(10000).Property(NAME_OF_JSON.time)]
    \nFor example: Path -> plugin://plugin.video.wl/?action=show&json=watchlist \nbecomes \nplugin://plugin.video.wl/?action=show&json=watchlist&t=$INFO\[Window(10000).Property(watchlist.time)].
    \nOmit the backslash after INFO.
    """
    xbmcgui.Dialog().textviewer('Info MyWatchlist',txt)

def setsetting(txt,setting):
    lists = list_json_lists()
    menu = []
    for x in lists:
        menu.append(x)
    heading = f"Select list for {txt}"
    sel = xbmcgui.Dialog().select(heading, menu)
    if sel > -1:
        ADDON.setSetting(setting,lists[sel])

def wl_file():
    txt = "watchlist"
    setting = "wl_list"
    setsetting(txt,setting)

def sc_file():
    txt = "secon button"
    setting = "sc_list"
    setsetting(txt,setting)

def rs_file():
    restore()

#wl_file()
#xbmcgui.Dialog().notification('DEBUG', 'test', xbmcgui.NOTIFICATION_INFO, 2000)

if sys.argv[1] == 'wl':
    wl_file()
elif sys.argv[1] == 'sc':
    sc_file()
elif sys.argv[1] == 'rs':
    rs_file()
elif sys.argv[1] == 'it':
    infotext()
