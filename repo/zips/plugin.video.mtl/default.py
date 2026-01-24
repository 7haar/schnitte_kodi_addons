#!/usr/bin/python
# -*- coding: utf-8 -*-

# MTL
# to do:
import os
import sys

import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmc
import xbmcaddon
from urllib.parse import parse_qs, unquote, quote, urlencode
from resources.lib import utils as u

from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib.request,urllib.error,urllib.parse
import json
import re
import time



ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
LANGID = ADDON.getLocalizedString
URL = sys.argv[0]
HANDLE = int(sys.argv[1])
WINDOW = xbmcgui.Window(10000)
#WINDOW = xbmcgui.Window(xbmcgui.getCurrentWindowId())
SETTING = ADDON.getSetting
_SEARCH_NAME_ = 'xxmtlxxsearch'
d = xbmcgui.Dialog()

# Get addon base path
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
IMG_DIR = os.path.join(ADDON_PATH, 'resources', 'images')

'''
def selectlist(label, list_items, details=False):
    while True:
        what = d.select(label, list_items, useDetails=details)
        if what == -1:
            return None
    return selected


def get_url(**kwargs):
    return '{}?{}'.format(URL, urllib.parse.urlencode(kwargs))
'''

def safe_list(items,list):
    items_list = []
    #d.ok('debug',str(items))
    for item in items['items']:
        item_data = {
                "channel": item['channel'],
                "title": item['title'],
                "topic":item['topic'],
                "thumb":item['thumb'],
                "fanart": item['fanart'],
                "landscape": item['landscape']
                }
        items_list.append(item_data)
    data = {
        'settings': items['settings'],
        'items': items_list
        }
    list_name = list
    if list == _SEARCH_NAME_:
        list_name = "Suche"
    if u.save_list(data,list):
        d.notification(list_name.upper(), f"Gespeichert", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        d.notification(list_name.upper(), f"Fehler beim Speichern", xbmcgui.NOTIFICATION_INFO, 2000)

def create_result_items(j):
    items = []
    for i in j['result']['results']:
        item = {}
        item["channel"] = i["channel"]
        item["topic"] = i["topic"]
        item["title"] = i["title"]
        #u.log_info(f"{item['topic']} _ {item['title']}")
        if item['topic'] not in item['title'] and "ARTE.DE" not in item["channel"]:
            #item['title'] = f"{item['topic']} | {item['title']}"
            item['title'] = f"{item['title']} | {item['topic']}"
        item["description"] = i["description"]
        item["timestamp"] = i["timestamp"]
        item["duration"] = i["duration"]
        item["url_website"] = i["url_website"]
        sources = [i.get("url_video_hd"),i.get("url_video"),i.get("url_video_low")]
        item["url_video"] = next((s for s in sources if s), None)
        item["url_video_alt"] = next((s for s in sources if s and s != item["url_video"]), None)
        items.append(item)
    return items

def create_item(query,channel=None):
    item = {}
    while not item:
        result = mvw_txt(query)
        result_items = create_result_items(result)
        #d.ok('debug',str(result))
        #d.ok('debug',str(result_items))
        titles = [f"{i.get('title','')} | {i.get('topic','')} | {i.get('channel','')}" for i in result_items if i.get('channel') == channel or channel is None]
        sel = d.select('Sendung wählen',titles)
        if sel == -1:
            # Abbrechen
            break
        else:
            item['channel'] = (result_items[sel].get('channel'))
            if result_items[sel].get('channel') == 'ARTE.DE':
                item['title'] = query
            else:
                item['title'] = (result_items[sel].get('topic'))
            item['topic'] = (result_items[sel].get('topic'))
            break
    return item

def search(s=None):
    if s:
        if "{" in s:
            return
        else:
            searchstring = s
    else:
        searchstring = WINDOW.getProperty('mtl.search') or d.input('..Suche..')
    if not searchstring:
        return
    WINDOW.setProperty('mtl.search', searchstring)
    items = {'settings':{},'items':[]}
    i = {}
    name = _SEARCH_NAME_
    items['settings']['fps'] = 1
    items['settings']['duration_min'] = 0
    items['settings']['static'] = ""
    i['channel'] = ''
    i['title'] = searchstring
    i['topic'] = ''
    i['thumb'] = ''
    i['fanart'] = ''
    i['landscape'] = ''
    items['items'].append(i)
    save = safe_list(items,name)
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    list_videos_switch(name)
    xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

def payload_s(data, size=50, dur=600):
    #u.log_info(str(data))
    channels = None
    if any('channel' in d and d['channel'] for d in data):
        channels = list({d['channel'] for d in data if 'channel' in d and d['channel']})
    #d.ok('debug',str(channels))
    payload = {
    'queries': (
        [{'fields': ['channel'], 'query': channel} for channel in channels] + 
        [{'fields': ['title', 'topic'], 'query': item['title']} for item in data]
        if channels else
        [{'fields': ['title', 'topic'], 'query': item['title']} for item in data]
    ),
    'sortBy': 'timestamp',
    'sortOrder': 'desc',
    'future': True,
    'offset': 0,
    'size': size,
    'duration_min': dur
    }
    #d.ok('debug payload_s',str(payload))    
    return payload



def mvw(payload):
    mvw_url = 'https://mediathekviewweb.de/api/query'
    params = json.dumps(payload).encode('utf8')
    req = urllib.request.Request(mvw_url, data=params,headers={'content-type': 'text/plain'})
    try:
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        notice('HTTPError = ' + str(e.code))
        d.notification('ERROR','mediathekviewweb.de nicht erreichbar',xbmcgui.NOTIFICATION_ERROR, 5000)
        return
    except urllib.error.URLError as e:
        notice('URLError = ' + str(e.reason))
        d.notification('ERROR','mediathekviewweb.de nicht erreichbar',xbmcgui.NOTIFICATION_ERROR, 5000)
        return
    j = json.loads(response.read())
    #u.log_info(str(j))
    #d.textviewer('debug response json mvw',str(j))
    ex_channel = ('ORF','SRF')
    j["result"]["results"] = [r for r in j["result"]["results"] if r.get("channel", "") not in ex_channel]
    return j


def sort_videos(videos,items,fps,search=False):
    #d.ok('size videos_sort',str(len(videos)))
    if search:
        return videos
    videos_sort = []
    list1 = []
    list2 = {}
    for topic in items:
        list1.append(topic['topic'])
    # Find duplicates using list comprehension
    dup = {value for value in list1 if list1.count(value) > 1}
    for item in items:
        if item['topic'] not in dup:
            key = item['topic']
        else:
            key = (item['topic'],item['title'])
        list2.setdefault(key, {'count': 0, 'item': item})
    #d.textviewer('debug',str(list2))
    #d.textviewer('name',str(items))    
    for video in videos:
        topic = video.get('topic')
        title = video.get('title')
        used_key = None
        name = ""
        out_list =("rdensprache)","Audiodeskription","Untertitel)","isch)","version)","(nld)","(OV)","(swe)")
        out = any(elem in title for elem in out_list)
        #pat = "\(.+\)"
        #out = bool(re.search(pat, title))
        if out:
            continue
        if topic in list2:
            used_key = topic
        else:
            for key in list2:
                if isinstance(key, tuple) and key[0].lower() == topic.lower():
                    name = key[1].lower()
                    if name in title.lower():
                        used_key = key
                        break
        #d.ok('debug',str(name))
        if used_key is None:
            continue
        if list2.get(used_key, {}).get('count', 0) >= fps:
            continue
        video['fanart'] = list2[used_key]['item']['fanart']
        video['landscape'] = list2[used_key]['item']['landscape']
        video['thumb'] = list2[used_key]['item']['thumb']
        videos_sort.append(video)
        list2[used_key]['count'] += 1
    return videos_sort


def mvw_list(name):
    search = False
    item_list = u.load_list(name)
    #d.ok('debug load_list nvw_list',str(item_list))
    items = []
    for item in item_list['items']:
        items.append({'channel':item['channel'],'title':item['title'],'topic':item['topic']})
    # Folgen pro Eintrag
    fps = int(item_list['settings']['fps'])
    # size
    size = fps * len(items) * 30
    dur = 60 * int(item_list['settings']['duration_min'])
    static = item_list['settings']['static']
    j = mvw(payload_s(items,size,dur))
    videos = create_result_items(j)
    #d.textviewer('debug',str(videos))
    if name == _SEARCH_NAME_:
        search = True
    videos_sort = sort_videos(videos, item_list['items'], fps, search)
    #d.textviewer('debug',str(videos_sort))
    
    return videos_sort, static

    
def mvw_txt(txt,tt=""):
    data = [{"title": txt}]
    j = mvw(payload_s(data))
    return j

def check_url(url, timeout=2):
    if not url:
        return False
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
             return 200 <= resp.getcode() < 400
    except Exception:
        return False

# ungenutzt
def get_player_times():
    active = json.loads(xbmc.executeJSONRPC(json.dumps({"jsonrpc":"2.0","method":"Player.GetActivePlayers","id":1}))).get("result", [])
    if not active:
        return 0, 0
    pid = active[0]["playerid"]
    props = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc":"2.0","method":"Player.GetProperties",
        "params":{"playerid": pid, "properties": ["time","totaltime"]},"id":1
    }))).get("result", {})
    t = props.get("time", {"hours":0,"minutes":0,"seconds":0})
    T = props.get("totaltime", {"hours":0,"minutes":0,"seconds":0})
    return t["hours"]*3600 + t["minutes"]*60 + t["seconds"], T["hours"]*3600 + T["minutes"]*60 + T["seconds"]


def playvideo(liste=None, stitle=None):
    player=xbmc.Player()
    if player.isPlaying():
        player.stop()
    list_res = u.load_list_res(liste)
    video = list_res.get(stitle, {})
    list_item = xbmcgui.ListItem(label=video.get('title'))
    list_item.setArt({'icon': video.get('thumb'),'landscape': video.get('landscape'),'fanart': video.get('fanart')})
    info_tag = list_item.getVideoInfoTag()
    info_tag.setMediaType('video')
    info_tag.setTitle(video.get('title'))
    info_tag.setPlot(video.get('plot'))
    info_tag.setDuration(int(video.get('duration', 0)))
    ### Resume kommt von Kodi ###
    #info_tag.setResumePoint(video.get('resume', 0), int(video.get('duration', 0)))
    #info_tag.setPlaycount(video.get('playcount', 0))
    info_tag.setGenres([video.get('genre')])
    info_tag.setPlotOutline(video.get('plot_outline'))
    info_tag.setFirstAired(video.get('first_aired'))
    list_item.setProperty('IsPlayable', 'true')
    path = video.get('video_url')
    alt = video.get('video_url_alt')
    if not check_url(path):
        path = alt
    list_item.setPath(path)
    
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=list_item)   
    
    #### RESUME POINT #####
    player = xbmc.Player()
    # warten bis player start
    while not player.isPlaying():
        xbmc.sleep(100)
    interval = 30
    while player.isPlaying():
        waitTime = time.time() + interval
        while player.isPlaying() and time.time() < waitTime: # Pause gilt als isPlaying
            list_res[stitle]['resume'] = round(player.getTime())
            xbmc.sleep(500)
            #d.notification("wiedergabe", f"time:{time.time()}|waitTime:{waitTime}|Interval:{interval}s", xbmcgui.NOTIFICATION_INFO, 100)
    if not player.isPlaying():
        player.stop()
        #d.textviewer('stop',str(list_res))
        if float(list_res[stitle]['resume']) > 0.9 * list_res[stitle]['duration']:
            list_res[stitle]['playcount'] = 1
            list_res[stitle]['resume'] = 0
        u.save_list(list_res,liste,'res')
        #d.notification("Stop", f"save resume", xbmcgui.NOTIFICATION_INFO, 2000)
    
def playvideo2(path,alt):
    play_item = xbmcgui.ListItem()
    if not check_url(path):
        path = alt
    #d.ok('debug playvideo',f"path:{path} alt:{alt}")
    play_item.setPath(path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)
    
################# IMG #######################
def image_select_dialog(img_list,label="Bild"):
    items = []
    #u.log_info(str(img_list))
    for i, path in enumerate(img_list):
        #path = path.split("?w=", 1)[0]
        li = xbmcgui.ListItem(label=f"{label} {i+1}")
        li.setArt({'thumb': path, 'icon': path, 'poster': path})
        items.append(li)
    sel = d.select(f"Wähle {label}", items, useDetails=True)
    if sel == -1:
        return None
    return img_list[sel]

def zdf_img_search(topic):
    #
    #under contruction
    #
    response = urllib.request.urlopen(req)
    j = json.loads(response.read())
    img_list = {'fanart': [],'landscape':[],'thumb':[]}
    return img_list

def ard_img_search(topic):
    url = f"https://api.ardmediathek.de/search-system/search/shows/ard?query={quote(topic)}&pageSize=20&platform=MEDIA_THEK"
    #d.ok('ard_img_search url',url)
    req = urllib.request.Request(url, data=None,headers={'content-type': 'text/plain'})
    response = urllib.request.urlopen(req)
    j = json.loads(response.read())
    img_list = {'fanart': [],'landscape':[],'thumb':[]}
    for teaser in j['teasers']:
        if (src := teaser.get('images', {}).get('aspect16x9', {}).get('src')): img_list['landscape'].append(src.split('?', 1)[0])
        if (src := teaser.get('images', {}).get('aspect16x7', {}).get('src')): img_list['fanart'].append(src.split('?', 1)[0])
        if (src := teaser.get('images', {}).get('aspect1x1', {}).get('src')): img_list['thumb'].append(src.split('?', 1)[0])
    return img_list

def arte_img_search(topic):
    token = "Bearer MWZmZjk5NjE1ODgxM2E0MTI2NzY4MzQ5MTZkOWVkYTA1M2U4YjM3NDM2MjEwMDllODRhMjIzZjQwNjBiNGYxYw"
    url = f"https://api-cdn.arte.tv/api/emac/v3/de/web/data/SEARCH_LISTING/?query={quote(topic)}&limit=20"
    req = urllib.request.Request(url, data=None,headers={'Content-Type': 'text/plain','Authorization': f'{token}','Accept': 'application/json'})
    response = urllib.request.urlopen(req)
    j = json.loads(response.read())
    img_list = {'fanart': [],'landscape':[],'thumb':[]}
    for item in j['data']:
        img_list['landscape'].append(f"{item['images']['landscape']['resolutions'][-2]['url']}?type=TEXT")
        img_list['fanart'].append(item['images']['landscape']['resolutions'][-1]['url'])
        img_list['thumb'].append(item['images']['square']['resolutions'][-1]['url'])
    #u.log_info(str(pretty))
    return img_list

def switch_img(url):
    #u.log_info(url)
    #d.ok('splitter',str(url))
    splitter = url.split('/')
    ard = "ard"
    arte = "arte"
    zdf = True
    sat = "3sat"
    kika = "kika"
    dw = "p.dw.com"
    if ard in splitter[2]:
        img_url = ard_img(splitter[-1])
    elif kika in splitter[2]:
        video_id = splitter[-1].replace(".html","")
        img_url = kika_img(video_id)
    elif arte in splitter[2]:
        img_url = arte_img(splitter[5])
    elif any(sub in splitter[2] for sub in ("3sat", "zdf")):
        video_id = splitter[-1].replace(".html","")
        if "3sat" in splitter[2]:
            zdf = False
        img_url = zdf_img(video_id,zdf)
    elif dw in splitter[2]:
        img_url = f"{IMG_DIR}/dw_logo.jpg"
    else:
        img_url = False
    #u.log_info(str(img_url))
    return img_url
    
def kika_img(url):
    video_id = url
    kikaapi_url = f"https://www.kika.de/_next-api/proxy/v1/videos/{video_id}"
    #d.ok('kika_img',kikaapi_url)
    req = urllib.request.Request(kikaapi_url, data=None,headers={'content-type': 'text/plain'})
    try:
        response = urllib.request.urlopen(req)
        j = json.loads(response.read())
        #d.textviewer(img_url'debug reimg_urlvw',str(j))
        img_url = f"https://www.kika.de{j['teaserImage']['urlScheme']}".replace("**imageVariant**","tlarge169").replace("**width**","1920")
        #d.ok('kika_img',str(img_url))
    except:
        img_url = False
    return img_url

def ard_img(url):
    video_id = url
    #d.ok('ard',video_id)
    ardapi_url = f"https://api.ardmediathek.de/page-gateway/mediacollection/{video_id}?devicetype=pc&embedded=true"
    req = urllib.request.Request(ardapi_url, data=None,headers={'content-type': 'text/plain'})
    try:
        response = urllib.request.urlopen(req, timeout=10)
        j = json.loads(response.read())
        #d.textviewer(img_url'debug reimg_urlvw',str(j))
        img_url = j['_previewImage']
    except:
        img_url = False
    return img_url

def arte_img(path):
    #u.log_info(path)
    video_id = path
    arteapi_url = f"https://api.arte.tv/api/player/v2/config/de/{video_id}"
    #d.ok('arte_img',arteapi_url)
    req = urllib.request.Request(arteapi_url, data=None,headers={'content-type': 'text/plain'})
    try:
        response = urllib.request.urlopen(req)
        j = json.loads(response.read())
        #d.textviewer(img_url'debug reimg_urlvw',str(j))
        img_url = f"{j['data']['attributes']['metadata']['images'][0]['url']}?type=TEXT"
    except:
        img_url = False
    return img_url

def zdf_img(url,z):
    img_url = False
    video_id = url
    zdfToken = "5bb200097db507149612d7d983131d06c79706d5"
    satToken = "13e717ac1ff5c811c72844cebd11fc59ecb8bc03"
    #zdfToken = "5bb200097db507149612d7d9"
    zdf_api = "api.zdf.de"
    sat_api = "api.3sat.de"
    zdf_url =f"https://api.zdf.de/content/documents/{video_id}.json"
    sat_url =f"https://api.3sat.de/content/documents/{video_id}.json"
    zdf = "zdf"
    sat = "3sat"
    if z:
        api_url = zdf_url
        host = zdf_api
        apitoken = zdfToken
        channel = zdf
    else:
        api_url = sat_url
        host = sat_api
        apitoken = satToken
        channel = sat
    for i in [0,2,4,6]:
        a_url = f"https://www.{channel}.de/assets/{video_id[:-3]}10{i}~1280x720"
        if u.is_reachable(a_url):
            img_url = a_url
            return img_url
        a_url = f"https://www.{channel}.de/assets/{video_id[:-3]}teaser-10{i}~1280x720"
        if u.is_reachable(a_url):
            img_url = a_url
            return img_url
    if not img_url:
        header = "{{'Api-Auth': 'Bearer {0}', 'Host': '{1}'}}".format(apitoken, host)
        header = header.replace("'", "\"")
        header = json.loads(header)
        #d.ok('zdf_img',video_id)
        req = urllib.request.Request(api_url, data=None,headers=header)
        try:
            response = urllib.request.urlopen(req)
            j = json.loads(response.read())
            #u.log_info(str(j))
            #img_url = j['teaserImageRef']['layouts']['1920x1080']
            img_url = (j.get('teaserImageRef')).get('layouts').get('1280x720', '1920x1080')
        except:
            img_url = False
    return img_url



#################

def listing():
    WINDOW.setProperty('mtl.listing', 'activate')
    WINDOW.clearProperty('mtl.search')
    lists = u.list_json_lists(_SEARCH_NAME_) # Suche wird nicht angezeigt
    xbmcplugin.setContent(HANDLE, 'videos')
    xbmcplugin.setPluginCategory(HANDLE, 'MTL')
    for list in lists:
        li = xbmcgui.ListItem(label=list, offscreen=True)
        info_tag = li.getVideoInfoTag()
        #info_tag.setMediaType('video')
        info_tag.setMediaType('tvshow')
        info_tag.setTitle(list.capitalize())
        url = f"plugin://{ADDON_ID}/?action=show&json={list}"
        is_folder = True
        remove_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=removelist&json={list})"
        editlist_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=newlist&json={list})"
        playlist_cmd = f"RunPlugin(plugin://{ADDON_ID}/?action=playlist&json={list})"
        #li.addContextMenuItems([(f"[COLOR goldenrod]play all[/COLOR]", playlist_cmd),(f"[COLOR goldenrod]edit list[/COLOR]", editlist_cmd),(f"[COLOR goldenrod]remove list[/COLOR]", remove_cmd)])
        li.addContextMenuItems([(f"[COLOR goldenrod]edit list[/COLOR]", editlist_cmd),(f"[COLOR goldenrod]remove list[/COLOR]", remove_cmd)])
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=is_folder)    
    li = xbmcgui.ListItem(label="...Liste erstellen")
    is_folder = True
    url = f"plugin://{ADDON_ID}/?action=newlist"
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=is_folder)
    ### SUCHE ###
    li = xbmcgui.ListItem(label="...Suche")
    is_folder = True
    url = f"plugin://{ADDON_ID}/?action=search&s="
    #url = f"plugin://{ADDON_ID}/?action=search_input"
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=is_folder)
    ###
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=False)

#DYNAMIC
def create_li(video, list_res, liste, static):
    try:
        ts = video.get('timestamp','')
        stitle = f"{video.get('title','')}{ts}"
        #lr = list_res.get(stitle, {})
        lr = list_res.get(stitle)
        if isinstance(lr, dict):
            lr_landscape = lr.get('landscape','')
            resume = lr.get('resume',0)
            playcount = lr.get('playcount',0)
        else:
            lr_landscape = None
            resume = 0
            playcount = 0
        landscape = None
        #d.textviewer('create_li static',f"{type(static)}|{str(lr)}")
        if not static and lr_landscape is None:
            landscape = switch_img(video['url_website'])
        if lr_landscape:
            landscape = lr_landscape
        landscape_item = landscape
        #landscape = switch_img(video['url_website'])
        #landscape = list_res.get(stitle, {}).get('landscape','')
        #d.textviewer("create_li",f"{stitle}|{landscape}")            
        if not landscape:
            landscape = video.get('landscape','')
        list_item = xbmcgui.ListItem(label=video['title'])
        list_item.setArt({
            'icon': video.get('thumb', ''),
            'landscape': landscape,
            'fanart': video.get('fanart', '')
        })
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType('video')
        info_tag.setTitle(video.get('title', ''))
        info_tag.setPlot(video.get('description', ''))
        info_tag.setDuration(int(video.get('duration', 0)))
        #info_tag.setResumePoint(float("120"), int(video.get('duration', 0))) # xxx funktioniert, spielt aber noch nicht bei 1 min ab
        info_tag.setResumePoint(resume, int(video.get('duration', 0)))
        info_tag.setPlaycount(playcount)
        info_tag.setGenres([video.get('channel', '')])
        info_tag.setPlotOutline(video.get('channel', ''))
        info_tag.setFirstAired(u.datum(video.get('timestamp')))
        list_item.setProperty('IsPlayable', 'true')
        video_url = video.get('url_video', '')
        video_url_alt = video.get('url_video_alt', '')
        url = f"plugin://{ADDON_ID}/?action=play&json={liste}&stitle={quote(stitle)}"
        #url = f"plugin://{ADDON_ID}/?action=play&file={video_url}&alt={video_url_alt}"
        item = {
                "list":liste,
                "media_type": "video",
                "title": video.get("title", ""),
                "plot": video.get("description", ""),
                "duration": int(video.get("duration", 0)),
                "genres": [video.get("channel", "")],
                "plot_outline": video.get("channel", ""),
                "first_aired": u.datum(video.get("timestamp")),
                "icon": video.get("thumb", ""),
                "landscape": landscape_item,
                "fanart": video.get("fanart", ""),
                "resume": resume,
                "playcount":playcount,
                "video_url": video_url,
                "video_url_alt": video_url_alt
                }
        res_item = (f"{video.get('title','')}{ts}",item)
        return (url, list_item, ts, res_item)
    except Exception as e:
        u.log_info(f"error creating info for {video.get('title')}: {e}")
        return None

def list_videos(videos, liste, static, max_workers=20):
    xbmcplugin.setContent(HANDLE, 'videos')
    items = []
    results = []
    list_res = u.load_list_res(liste)
    #d.textviewer('list_res',str(list_res))
    temp = {}
    list_name = liste
    if liste == _SEARCH_NAME_:
        list_name = "Suche"
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(create_li, v, list_res, liste, static): v for v in videos}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)
    results.sort(key=lambda item: int(item[2]), reverse=True)
    #d.textviewer('debug',str(results))
    if results:
        for url, list_item, ts, res_item in results:
            #u.log_info(str(res_item))
            a,b = res_item
            temp[a] = b
            try:
                xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)
            except Exception as e:
                u.log_error(f"addDirectoryItem error: {e}")
        if temp != list_res:
            u.save_list(temp,liste,'res')
        xbmcplugin.endOfDirectory(HANDLE)
    else:
        d.notification(list_name, "keine Ergebnisse", xbmcgui.NOTIFICATION_INFO, 2000)


#STATIC

def list_videos_static(videos):
    xbmcplugin.setContent(HANDLE, 'videos')
    for video in videos:
        list_item = xbmcgui.ListItem(label=video['title'])
        list_item.setArt({'icon': video['thumb'],'landscape': video['landscape'],'fanart':video['fanart']})
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType('video')
        info_tag.setTitle(video['title'])
        info_tag.setPlot(video['description'])
        info_tag.setDuration(int(video['duration']))
        info_tag.setGenres([video.get('channel', '')])
        info_tag.setPlotOutline(video.get('channel', ''))
        info_tag.setFirstAired(u.datum(video.get('timestamp')))
        list_item.setProperty('IsPlayable', 'true')
        #d.ok('list_videos video url',video['url_video'])
        video_url = quote(video['url_video'])
        video_url_alt = quote(video['url_video_alt'])
        #url = f"plugin://{ADDON_ID}/?action=play&json={video.get('list','')}&stitle={stitle}"
        url = f"plugin://{ADDON_ID}/?action=play2&file={video_url}&alt={video_url_alt}"
        #u.log_info(url)
        is_folder = False
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    '''
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    '''
    xbmcplugin.endOfDirectory(HANDLE)

#List video Switch
def list_videos_switch(list):
    videos, static = mvw_list(list)
    '''
    if static:
        list_videos_static(videos)
    else:
        list_videos(videos,list)
    '''
    list_videos(videos,list,static)
    
#NEW LIST
def newlist(json=None):
    items = {'settings':{},'items':[]}
    fps = 1
    dur = 10
    static = True
    menu = ['... Sendung hinzufügen']
    menu.append('... Liste speichern')
    menu.append('... Minimallänge in Minuten')
    menu.append('... Folgen pro Sendung (max 50)')
    menu.append('... Landscape: statisch')
    lng = len(menu)
    if json:
        name = json
        item_list = u.load_list(name)
        for item in item_list['items']:
            items['items'].append(item)
            menu.append(item['title'])
        fps = item_list['settings']['fps']
        dur = item_list['settings']['duration_min']
        static = item_list['settings']['static'] or ''
        menu[0] = f"... Sendung hinzufügen: aktuell {len(items['items'])}"
        menu[2] = f".. Minimallänge: {dur} min"
        menu[3] = f".. Folgen pro Sendung: {fps}"
        menu[4] = f".. Landscape: {'statisch' if static else 'dynamisch'}"
    else:
        name = u.clean_str(d.input('Name der neuen Liste'))
        if name == "":
            return
        else:
            lists = u.list_json_lists()
            if name in lists:
                d.notification(name,f"Schon vorhanden",xbmcgui.NOTIFICATION_ERROR, 2000)
                return
    #d.ok('debug MTL',name)
    while True:
        #d.ok('debug items newlist',str(items))
        menu[0] = f"... Sendung hinzufügen: aktuell {len(items['items'])}"
        what = d.select(name,menu)
        if what == -1:
            # Abbrechen / abfrage einbauen xxx
            break
        elif what == 0:
            # ...Sendung hinzufügen
            searchstring = (d.input('Name der Sendung'))
            if searchstring:
                send = create_item(searchstring)
                #d.ok('debug newlist send',str(send))
                if send:
                    if 'arte' in send['channel'].lower():
                        img_list = arte_img_search(send['title'])
                        send['channel'] = "ARTE.DE"
                    elif send['topic'].lower() != send['title'].lower():
                        img_list = ard_img_search(send['title'])
                    else:
                        img_list = ard_img_search(send['topic'])
                    send['fanart'] = image_select_dialog(img_list['fanart'],'Fanart')
                    send['landscape'] = image_select_dialog(img_list['landscape'],'Landscape')
                    send['thumb'] = image_select_dialog(img_list['thumb'],'Thumb')
                    items['items'].append(send)
                    menu.append(f"{send.get('title')}")
                    #d.textviewer('test ard_img_search',str(ard_img_search(send['topic'])))
        # Speichern
        elif what == 1:
            if len(items['items']) > 0:
                items['settings']['fps'] = fps
                items['settings']['duration_min'] = dur
                items['settings']['static'] = static
                #u.log_info(str(items))
                save = safe_list(items,name)
            else:
                d.notification(name, "nicht gespeichert - keine Sendungen eingetragen", xbmcgui.NOTIFICATION_INFO, 2000)
            break
        # duration_min
        elif what == 2:
            dur = d.numeric(0,"Minimallänge in Minuten")
            if dur:
                dur = int(dur)
                menu[2] = f".. Minimallänge: {dur}"
        # fps    
        elif what == 3:
            fps = d.numeric(0,"Folgen pro Sendung (max 50)")
            if fps and int(fps) < 51:
                fps = int(fps)
                menu[3] = f".. Folgen pro Sendung: {fps}"
        elif what == 4:
            static = d.yesno("Landscape", "Statisch aus der JSON-Liste \nDynamisch aus den Mediatheken", "Dynamisch", "Statisch",0,xbmcgui.DLG_YESNO_YES_BTN)
            menu[4] = f".. Landscape: {'statisch' if static else 'dynamisch'}"
        elif (what > lng-1):
            #d.ok('edit', str(list(items[what-lng].values())))
            # item edit
            while True:
                list_keys = list(items['items'][what-lng])
                list_values = list(items['items'][what-lng].values())
                edit_menu = []
                for i,key in enumerate(list_keys):
                    s = f"{key}: {list_values[i]}"
                    edit_menu.append(s)            
                edit_sel = d.select(menu[what],edit_menu)
                if edit_sel == -1:
                    break
                if edit_sel == 1:                    
                    ync = d.yesnocustom(menu[what],f"Testen / Umbenennen - {menu[what]}\nFolgen pro Sendung: {fps} - Minimallänge: {dur} min", "Testen", "Löschen", "Umbenennen",0,xbmcgui.DLG_YESNO_YES_BTN ) #201
                    # Testen
                    if ync == 2:
                        test_titles = ""
                        result = mvw(payload_s([items['items'][what-lng]],fps,dur*60))
                        for i in result['result']['results']:
                            test_titles = f"{test_titles} {i['title']} | min: {round(int(i['duration'])/60)}\n"
                        # bearbeiten xxx
                        d.textviewer(f"Ergebnisse für {menu[what]}",test_titles)
                    # Umbennen
                    if ync == 1:
                        new = d.input('Name der Sendung',items['items'][what-lng]['title'])
                        if new:
                            send = create_item(new,items['items'][what-lng]['channel'])
                            #d.ok('debug newlist send',str(send))
                            if send:
                                items['items'][what-lng]['title'] = new
                                items['items'][what-lng]['topic'] = send['topic']
                                menu[what] = f"{new}"
                    if ync == 0:
                       del items['items'][what-lng]
                       del menu[what]
                       break
                if edit_sel > 2:
                    if items['items'][what-lng]['channel'] == "ARTE.DE":
                        img_list = arte_img_search(items['items'][what-lng]['title'])
                    elif items['items'][what-lng]['topic'] != items['items'][what-lng]['title']:
                        img_list = ard_img_search(items['items'][what-lng]['title'])
                    else:
                        img_list = ard_img_search(items['items'][what-lng]['topic'])
                    items['items'][what-lng][list_keys[edit_sel]] = image_select_dialog(img_list[list_keys[edit_sel]],list_keys[edit_sel])
                    
                    
                    
def remove_list(list):
    perm = ADDON.getSetting('perm') == 'true'
    dl = u.delete_file(f"{list}.json",perm)
    if dl:
        d.notification(f"{str(list).upper()}", f"...entfernt", xbmcgui.NOTIFICATION_INFO, 2000)
    else:
        d.notification(f"{str(list).upper()}", f"Fehler beim Entfernen", xbmcgui.NOTIFICATION_INFO, 2000)
    xbmc.executebuiltin("Container.Refresh")

#######################

def router(paramstring):
    params = parse_qs(paramstring[1:])
    action = params.get('action', [None])[0]
    file_path = params.get('file', [''])[0]    
    file_path_alt = params.get('alt', [''])[0]    
    json = params.get('json', [None])[0]
    stitle = params.get('stitle', [None])[0]
    #d.ok('router',f"{json}|{stitle}")
    s = params.get('s', [None])[0]
    if action == "newlist":
        newlist(json)
    elif action == "remove":
        remove_from_watchlist(file_path,json)
    elif action == "removelist":
        remove_list(json)
    elif action == "play":
        playvideo(json,stitle)
    elif action == "play2":
        playvideo(file_path,file_path_alt)
    elif action == "show":
        list_videos_switch(json)
    elif action == "playlist":
        playlist(json)
    elif action == "search_input":
        search_input()  
    elif action == "search":
        search(s)
    else:
        listing()

if __name__ == '__main__':
    router(sys.argv[2])

