import os
import json
import re
import xbmcvfs
import xbmcgui
import xbmcaddon

ADDON = xbmcaddon.Addon()  
ADDON_ID = "plugin.video.wl"
LANGID = ADDON.getLocalizedString
DATA_PATH = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}/")

#WATCHLIST_FILE = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}/watchlist.json")
#DATA_PATH = os.path.dirname(WATCHLIST_FILE)
#DATA_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

def delete_file(file,perm):
    try:
        path = os.path.join(DATA_PATH, file)
        if not os.path.isfile(path):
            return False
        if perm:
            os.remove(path)
        else:
            # umbenennen
            dir, file = os.path.split(path)
            name, ext = os.path.splitext(file)
            new_name = f"{name}.baq"
            new_path = os.path.join(dir, new_name)
            os.rename(path, new_path)
        return True
    except Exception as e:
        return False

def restore():
    menu = []
    lists = list_json_lists(".baq")
    if len(lists) > 0:
        heading = f"{LANGID(30215)}"
        menu.append(f"{LANGID(30216)}")
        for item in lists:
            menu.append(item)
        sel = xbmcgui.Dialog().select(heading, menu)
        if sel == 0:
            for item in lists:
                old_name = f"{item}.baq"
                new_name = f"{item}.json"
                old_path = os.path.join(DATA_PATH, old_name)
                new_path = os.path.join(DATA_PATH, new_name)
                os.rename(old_path, new_path)
            xbmcgui.Dialog().notification(f"{LANGID(30100)}", f"{LANGID(30217)}", xbmcgui.NOTIFICATION_INFO, 2000)
        elif sel > 0:
            it = lists[sel-1]
            old_name = f"{it}.baq"
            new_name = f"{it}.json"
            old_path = os.path.join(DATA_PATH, old_name)
            new_path = os.path.join(DATA_PATH, new_name)
            os.rename(old_path, new_path)
            xbmcgui.Dialog().notification(f"{LANGID(30100)}", f"{it} {LANGID(30218)}", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        xbmcgui.Dialog().notification(f"{LANGID(30100)}", f"{LANGID(30219)}", xbmcgui.NOTIFICATION_INFO, 2000)


def clean_str(s):
    return re.sub(r'[^A-Za-z0-9]', '', s)

def npath(path):
    if not path:
        return ""
    return os.path.normpath(path).replace("\\", "/").lower()

def ensure_data_path():
    if not xbmcvfs.exists(DATA_PATH):
        xbmcvfs.mkdir(DATA_PATH)

def list_json_lists(ext=".json"):
    ensure_data_path()
    files = []
    # xbmcvfs.listdir gibt (files, dirs)
    files = next(os.walk(DATA_PATH), (None, None, []))[2]
    #xbmcgui.Dialog().ok("WL", str(files))
    names = [os.path.splitext(f)[0] for f in files if f.lower().endswith(ext)]
    names.sort()
    return names

# --------------------------------------------------------
# JSON-Helper
# --------------------------------------------------------
def load_watchlist(list):
    #xbmcgui.Dialog().ok("Watchlist", name)
    name = f"{list}.json"
    fullfilepath = os.path.join(DATA_PATH, name)
    if not os.path.exists(fullfilepath):
        return []
    with open(fullfilepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_watchlist(data, list):
    name = f"{list}.json".lower()
    try:
        os.makedirs(DATA_PATH, exist_ok=True)
        fullfilepath = os.path.join(DATA_PATH, name)
        with open(fullfilepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        return False        
