import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import json
import os
import sys
import time
import re
from urllib.parse import parse_qs, unquote, quote, urlencode
from lib.utils import save_watchlist, load_watchlist, npath, list_json_lists, clean_str, delete_file

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
LANGID = ADDON.getLocalizedString
HANDLE = int(sys.argv[1])
WINDOW = xbmcgui.Window(10000)
IMG_PATH = xbmcvfs.translatePath(f"special://home/addons/{ADDON_ID}/resources/images/")

auto_sort = ADDON.getSetting('sort') == "2"

#DATA_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
#WATCHLIST_FILE = os.path.join(DATA_PATH, 'watchlist.json')

# Widget Update
#    # damit es funktioniert, muss im Skin t=$INFO[Window(10000).Property(NAME_DER_JSON.time)] in die URL eingetragen werden
#    # ah2mod skinshortcuts -> script-skinshortcuts-includes.xml
#    # oder bei Erstellung in Kodi den Pfad entsprechend bearbeiten: ..aktion -> watchlist wählen -> benutzerdefinierter eintrag -> bearbeiten 
    
# --------------------------------------------------------
# Watchlist-Funktionen
# --------------------------------------------------------

def file_info(path):
    dir, file = os.path.split(path)
    name, ext = os.path.splitext(file)
    info = {}
    info['dir'] = dir
    info['file'] = file
    info['name'] = name
    info['ext'] = ext
    return info 

def update(list):
    timestamp_sec = int(time.time())
    WINDOW.setProperty(f"{list}.time", str(timestamp_sec))

def playlist(list):
    watchlist = load_watchlist(list)
    # hier weiter
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear() 
    for item in watchlist:
        if item.get('fileorfolder') == "file":
            li = xbmcgui.ListItem(label=item.get('title', 'unknown'))
            li.setArt({'thumbnail':item.get('thumb'),'fanart':item.get('fanart'),'poster':item.get('poster'),'landscape':item.get('landscape'),'icon':item.get('thumb')})
            info = li.getVideoInfoTag()
            info.setTitle(item.get('title', 'unknown'))
            info.setPlot(item.get('plot', ''))
            if item.get('year'):
                try:
                    info.setYear(int(item['year']))
                except ValueError:
                    pass
            playlist.add(url=item.get('path'), listitem=li)
    if playlist.size() == 0:
        #xbmc.log("Playlist ist leer", level=xbmc.LOGDEBUG)
        # optional: Hinweis für Nutzer
        xbmcgui.Dialog().notification(f"{LANGID(30100)}", f"{LANGID(30201)}", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        player = xbmc.Player()
        player.play(playlist)
    
def add_to_watchlist():
    li = xbmcgui.ListItem()
    info = li.getVideoInfoTag()
    title = xbmc.getInfoLabel("ListItem.Label") or info.getTitle()
    plot = info.getPlot() or xbmc.getInfoLabel("ListItem.Plot") or title
    year = info.getYear() or xbmc.getInfoLabel("ListItem.Year")
    path = xbmc.getInfoLabel("ListItem.FileNameAndPath") or xbmc.getInfoLabel('ListItem.FolderPath')
    poster = xbmc.getInfoLabel("ListItem.Art(poster)")
    fanart = xbmc.getInfoLabel("ListItem.Art(fanart)")
    landscape = xbmc.getInfoLabel('ListItem.Art(landscape)') or fanart
    thumb = xbmc.getInfoLabel("ListItem.Thumb") or landscape
    is_playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == "true"
    DBTYPE = xbmc.getInfoLabel('ListItem.DBTYPE')
    
    
    VIDEO_TYPES = ("episode", "episodes", "movie", "movies", "video")
    fileorfolder = "folder"
    #filetype = "x"

    if DBTYPE:
        if DBTYPE.lower() in VIDEO_TYPES:
            #filetype = DBTYPE.lower()
            fileorfolder = 'file'
    elif path.startswith("pvr://"):
        fileorfolder = 'file'
    #DEBUG
    #debug = "Playable: " + str(is_playable) + "\nDBTYPE: " + str(DBTYPE) + "\nfiletype: " + str(fileorfolder)
    #xbmcgui.Dialog().ok('DEBUG',debug)
    
    item = {
        "title": title,
        "year": year,
        "plot": plot,
        "path": path,
        "thumb": thumb,
        "poster": poster,
        "fanart": fanart,
        "landscape": landscape,
        "fileorfolder": fileorfolder,
        "last_used": int(time.time())
    }
    but_bool = ADDON.getSetting('2but_bool') == 'true' 
    wlfile = ADDON.getSetting('wl_list')
    # DEBUG
    #xbmcgui.Dialog().ok('debug',f"{wlfile['name']} | {wlfile['dir']}" )
    #
    menu = []
    files = list_json_lists()
    menu.append(f"[COLOR goldenrod]{LANGID(30202)}[/COLOR]") #sel = 0
    #menu.append('----------------- ADD TO -----------------------') #  sel = 1
    for x in files:
        menu.append(x)
    heading = f"MyWatchlist - {LANGID(30203)}"
    if but_bool:
        but = ADDON.getSetting('sc_list') # 2 0 1
        pre = xbmcgui.Dialog().yesnocustom(heading, f"Add {item['title']}", f"{LANGID(30203)} {wlfile.upper()}", f"{LANGID(30204)}", f"{LANGID(30203)} {but.upper()}", defaultbutton=xbmcgui.DLG_YESNO_CUSTOM_BTN)
    else:
        pre = xbmcgui.Dialog().yesnocustom(heading, f"Add {item['title']}", f"{LANGID(30203)} {wlfile.upper()}", f"{LANGID(222)}", f"{LANGID(30204)}", defaultbutton=xbmcgui.DLG_YESNO_CUSTOM_BTN)
    # DEBUG
    #xbmcgui.Dialog().ok("DEBUG",str(pre))
    if but_bool and pre == 1:
        target_name = but
        pre = 4
    elif but_bool and pre == 0:
        pre = 1

    if pre == 1:
        sel = xbmcgui.Dialog().select(heading, menu)
        if sel == -1:
            return
        if sel == 0:
            new_name = xbmcgui.Dialog().input(f"{LANGID(30205)}")
            if not new_name:
                return
            new_name = clean_str(new_name.strip())
            target_name = new_name
        else:
            target_name = menu[sel]
    elif pre == 2:
        target_name = wlfile
    elif pre == 4:
        pass
    else:
        return
    update(target_name)
    filename = target_name

    watchlist = load_watchlist(filename)
    # Doppelte vermeiden
    if not any(npath(x.get('path')) == npath(path) for x in watchlist):
        watchlist.append(item)
        if save_watchlist(watchlist,filename):
            xbmcgui.Dialog().notification(target_name.upper(), f"'{title}' {LANGID(30200)}", xbmcgui.NOTIFICATION_INFO, 2000)
        else:
            xbmcgui.Dialog().notification(target_name.upper(), f"'{title}' {LANGID(30206)}", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        xbmcgui.Dialog().notification(target_name.upper(), f"'{title}' {LANGID(30207)}", xbmcgui.NOTIFICATION_INFO, 2000)

def listing():
    lists = list_json_lists()
    xbmcplugin.setContent(HANDLE, 'tvshows')
    xbmcplugin.setPluginCategory(HANDLE, 'MyWatchlist')
    for list in lists:
        li = xbmcgui.ListItem(label=list, offscreen=True)
        fanart = os.path.join(IMG_PATH, f"fanart.jpg")
        img = os.path.join(IMG_PATH, f"{list[0]}.png") or os.path.join(IMG_PATH, f"star.png") 
        li.setArt({'icon':img,'fanart':fanart,'thumbnail':img})
        info_tag = li.getVideoInfoTag()
        info_tag.setMediaType('video')
        info_tag.setTitle(list.capitalize())
        url = f"plugin://{ADDON_ID}/?action=show&json={list}"
        is_folder = True
        remove_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=removelist&json={list})"
        playlist_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=playlist&json={list})"
        #script_cmd = "RunScript(plugin.video.wl)"
        li.addContextMenuItems([(f"[COLOR goldenrod]{LANGID(30208)}[/COLOR]", remove_cmd),(f"[COLOR goldenrod]{LANGID(30209)}[/COLOR]", playlist_cmd)])
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=is_folder)
        
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)

def show_watchlist(list):
    xbmcplugin.setContent(HANDLE, 'videos')
    xbmcplugin.setPluginCategory(HANDLE, f"MyWatchlist - {str(list).upper()}")
    if auto_sort:
        watchlist = sorted(load_watchlist(list), key=lambda x: x.get("last_used", 0), reverse=True)
    else:
        watchlist = load_watchlist(list)
    
    
    if not watchlist:
        xbmcgui.Dialog().notification(str(list).upper(), f"{LANGID(30210)}", xbmcgui.NOTIFICATION_INFO, 2000)
        xbmcplugin.endOfDirectory(HANDLE)
        return
    
    for item in watchlist:
        li = xbmcgui.ListItem(label=item.get('title', 'unknown'), offscreen=True)
        li.setArt({'thumbnail':item.get('thumb'),'fanart':item.get('fanart'),'poster':item.get('poster'),'landscape':item.get('landscape'),'icon':item.get('thumb')})
        info = li.getVideoInfoTag()
        info.setTitle(item.get('title', 'unknown'))
        info.setPlot(item.get('plot', ''))
        if item.get('year'):
            try:
                info.setYear(int(item['year']))
            except ValueError:
                pass
        
        if item['fileorfolder'] == "file":
            li.setProperty('IsPlayable', 'true')
            mt = "movie"
            is_folder = False
        else:
            li.setProperty('IsPlayable', 'false')
            mt = "tvshow"
            #is_folder = True
            is_folder = False
        
        info.setMediaType(mt)
        
        # Kontextmenü:
        encoded_path = quote(item['path'], safe='')
        remove_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=remove&json={list}&file={encoded_path})"
        playlist_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=playlist&json={list})"
        li.addContextMenuItems([(f"[COLOR goldenrod]{LANGID(30211)} {list}[/COLOR]", remove_cmd),(f"[COLOR goldenrod]{LANGID(30209)}[/COLOR]", playlist_cmd)])
        
        url = f"plugin://{ADDON_ID}/?action=play_switch&json={list}&file={encoded_path}"
        
        #url = f'plugin://script.openpath/?path={encoded_path}'
        #url = f'RunPlugin(plugin://script.openpath/?path={encoded_path})'
        
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=is_folder)
    
    if not auto_sort:
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
        #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_NONE)
        
    xbmcplugin.endOfDirectory(HANDLE,succeeded = True, updateListing = False)

def remove_list(list):
    perm = ADDON.getSetting('perm') == 'true'
    dl = delete_file(f"{list}.json",perm)
    if dl:
        xbmcgui.Dialog().notification(f"{str(list).upper()}", f"{LANGID(30212)}", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        xbmcgui.Dialog().notification(f"{str(list).upper()}", f"{LANGID(30213)}", xbmcgui.NOTIFICATION_INFO, 2000)
    xbmc.executebuiltin("Container.Refresh")
    
def remove_from_watchlist(file_path, list):
    #xbmcgui.Dialog().ok('Pfad',file_path)
    update(list)
    watchlist = load_watchlist(list)
    new_list = []
    for item in watchlist:
        #xbmcgui.Dialog().ok('Pfad',item['path'] + "\n" + file_path)
        if item['path'] != file_path:
            new_list.append(item)
    save_watchlist(new_list, list)
    xbmcgui.Dialog().notification(f"{str(list).upper()}", f"{LANGID(30214)}", xbmcgui.NOTIFICATION_INFO, 2000)
    xbmc.executebuiltin("Container.Refresh")

def play_switch(file_path,list):
    #xbmcgui.Dialog().ok('debug',file_path)
    #xbmc.log(f"<<< WL >>>:play_switch file_path: {file_path}", level=xbmc.LOGINFO)
    update(list)
    watchlist = load_watchlist(list)
    full = ''
    for item in watchlist:
        if npath(item['path']) == npath(file_path):
            item['last_used'] = int(time.time())
            thumbnail = item['thumb']
            fanart = item['fanart']
            poster = item['poster']
            landscape = item['landscape']
            name = item['title']
            plot = item['plot']
            fileorfolder = item['fileorfolder']
            #path = item['path']
            break
    save_watchlist(watchlist,list)
    aw = ("plugin://","videodb://")
    if fileorfolder == 'folder':
        if file_path.startswith('addons://'):
            match = re.match(r'addons:\/\/user\/(.*)', file_path)
            addon_id = match.group(1)
            full = 'RunAddon(%s)' % addon_id
        #elif file_path.startswith('plugin://'): 
        elif any(file_path.startswith(sw) for sw in aw):
            epath = quote(file_path, safe=':/?&=%')
            full = f'ActivateWindow(10025,"{epath}",return)'
            
        # DEBUG
        #xbmcgui.Dialog().ok('debug',full)
        
        xbmcplugin.endOfDirectory(HANDLE,succeeded = True)
        if xbmc.getCondVisibility('Window.IsActive(10000)'):
            xbmc.executebuiltin('ActivateWindow(Home)')
        xbmc.executebuiltin('Dialog.Close(all, true)')
        xbmc.executebuiltin('Container.Close')
        xbmc.executebuiltin(full)
        return
    
    if fileorfolder == 'file':
        path = file_path
        if path.lower().endswith('.strm') and xbmcvfs.exists(path):
            with xbmcvfs.File(path) as f:
                path = f.read().strip()
        if path.startswith('smb://'):
            prefix = 'smb://'
            ppath = path[len(prefix):]
            epath = quote(ppath)
            use_path = prefix + epath 
        elif path.startswith('special://'):
            rpath = xbmcvfs.translatePath(path)
            use_path = f'file://{quote(rpath)}'
        else:
            use_path = path
        play_item = xbmcgui.ListItem(offscreen=True)
        play_item.setPath(use_path)
        play_item.setLabel(name)
        play_item.setArt({'thumbnail':thumbnail,'fanart':fanart,'poster':poster,'landscape':thumbnail})
        info_tag = play_item.getVideoInfoTag()
        info_tag.setPlot(plot)
        if use_path.startswith('pvr://'):
            xbmc.executebuiltin(f"PlayMedia({use_path})")
        else:
            try:
                xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)
            except:
                xbmc.executebuiltin(f"PlayMedia({use_path})")            

# --------------------------------------------------------
# Router
# --------------------------------------------------------
def router(paramstring):
    params = parse_qs(paramstring[1:])
    action = params.get('action', [None])[0]
    
    fp = params.get('file', [''])[0]
    #xbmc.log(f"<<< WL >>>:play_switch file_path vor unquote: {fp}", level=xbmc.LOGINFO)
    
    file_path = fp
    #file_path = unquote(params.get('file', [''])[0])
    #file_path = unquote(unquote(params.get('file', [''])[0]))
    json = params.get('json', [None])[0]
    if json:
        WINDOW.setProperty(f"{json}.time", '0')
    #DEBUG
    #xbmcgui.Dialog().ok('debug',str(auto_sort))
    #xbmc.log(f"<<< WL >>>:play_switch file_path nach unquote: {file_path}", level=xbmc.LOGINFO)
    
    
    if action == "add":
        add_to_watchlist()
    elif action == "remove":
        remove_from_watchlist(file_path,json)
    elif action == "removelist":
        remove_list(json)
    elif action == "play_switch":
        play_switch(file_path,json)
    elif action == "show":
        show_watchlist(json)
    elif action == "playlist":
        playlist(json)
    else:
        listing()

if __name__ == '__main__':
    router(sys.argv[2])
