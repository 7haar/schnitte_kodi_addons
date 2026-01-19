import os
import json
import re
import xbmcvfs
import xbmcgui
import xbmcaddon
import xbmc
import datetime
import requests
#from contextlib import contextmanager

ADDON = xbmcaddon.Addon()  
ADDON_ID = ADDON.getAddonInfo('id')
LANGID = ADDON.getLocalizedString
DATA_PATH = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}/")
'''
@contextmanager
def busy_spinner():
    xbmc.executebuiltin('Dialog.Update')
    xbmc.executebuiltin('ActivateWindow(10138)')  # Busy spinner on
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(10138)')  # Busy spinner off
'''

def debug_txt(txt):
    d = xbmcgui.Dialog()
    d.textviewer('debug', txt)

def debug_ok(txt):
    d = xbmcgui.Dialog()
    d.ok('debug', txt)

def log_info(txt):
    xbmc.log(repr(">>>>>>> " + txt),xbmc.LOGINFO)

#WATCHLIST_FILE = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}/watchlist.json")
#DATA_PATH = os.path.dirname(WATCHLIST_FILE)
#DATA_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))

def datum(tim):
    return datetime.datetime.fromtimestamp(int(tim)).strftime('%d.%m.%Y')

def ensure_data_path():
    if not xbmcvfs.exists(DATA_PATH):
        xbmcvfs.mkdir(DATA_PATH)

def list_json_lists(out="", ext=".json"):
    ensure_data_path()
    files = next(os.walk(DATA_PATH), (None, None, []))[2]
    names = []
    for f in files:
        try:
            if f.lower().endswith(ext):
                name = os.path.splitext(f)[0]
                if out and name == out:
                    continue
                names.append(name)
        except Exception:
            # Fehlerhafte Einträge überspringen
            continue
    names.sort()
    return names

def load_list_res(list):
    list_res = load_list(list,"res")
    return list_res

def load_list(list,ext="json"):
    #xbmcgui.Dialog().ok("Watchlist", name)
    name = f"{list}.{ext}"
    fullfilepath = os.path.join(DATA_PATH, name)
    if not os.path.exists(fullfilepath):
        #return []
        return {}
    with open(fullfilepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_list(data, list,ext="json"):
    name = f"{list}.{ext}".lower()
    try:
        os.makedirs(DATA_PATH, exist_ok=True)
        fullfilepath = os.path.join(DATA_PATH, name)
        with open(fullfilepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        return False        

def delete_file(file,perm=False):
    try:
        path = os.path.join(DATA_PATH, file)
        if not os.path.isfile(path):
            return False
        if perm:
            os.remove(path)
        else:
            # umbenennen
                    # xxx prüfen auf schon vorhanden noch integrieren
            dir, file = os.path.split(path)
            name, ext = os.path.splitext(file)
            new_name = f"{name}.baq"
            new_path = os.path.join(dir, new_name)
            os.rename(path, new_path)
        return True
    except Exception as e:
        return False

def is_reachable(s, timeout=2):
    try:
        r = requests.get(s, timeout=timeout, allow_redirects=False)
        status = r.status_code
        ctype = r.headers.get("Content-Type", "")
        ok = (status == 200) and "image" in ctype.lower()
        return ok
    except requests.exceptions.RequestException:
        return False

##############################################################################################################

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
