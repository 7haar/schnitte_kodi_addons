import sys
import xbmcgui
import xbmcaddon
from utils import list_json_lists, restore

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')

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
