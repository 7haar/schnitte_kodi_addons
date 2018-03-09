import re
import cProfile
import urllib, urllib2, cookielib, shutil,json, os
import sys
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs
#from io import StringIO, BytesIO
#from HTMLParser import HTMLParser
#from bs4 import BeautifulSoup
#import xml.etree.ElementTree as etree
#from lxml import etree
from django.utils.encoding import smart_str
from operator import itemgetter


# Setting Variablen des Plugins
global debuging
addon_handle = int(sys.argv[1])
addon = xbmcaddon.Addon()

main_url = "http://www.checkeins.de"

icon = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/icon.png').decode('utf-8') 

xbmcplugin.setContent(addon_handle, 'movies')
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)

# Cookie Section

profile = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

if xbmcvfs.exists(temp):
	shutil.rmtree(temp)
xbmcvfs.mkdirs(temp)

cookie=os.path.join( temp, 'cookie.jar')
cj = cookielib.LWPCookieJar();

if xbmcvfs.exists(cookie):
    cj.load(cookie,ignore_discard=True, ignore_expires=True)       

# ## #

def debug(content):
    log(content, xbmc.LOGDEBUG)

def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
	
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

	
def addDir(name, url, mode, thump, desc="",page=1,nosub=0):   
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&nosub="+str(nosub)
  ok = True
  liz = xbmcgui.ListItem(name)  
  liz.setArt({ 'fanart' : thump })
  liz.setArt({ 'thumb' : thump })
  liz.setArt({ 'banner' : icon })
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok
  
def addLink(name, url, mode, thump, duration="", desc="", genre='',director="",bewertung=""):
  debug("URL ADDLINK :"+url)
  debug( icon  )
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
  ok = True
  liz = xbmcgui.ListItem(name,thumbnailImage=thump)
  liz.setArt({ 'fanart' : icon })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Genre": genre, "Director":director,"Rating":bewertung})
  liz.setProperty('IsPlayable', 'true')
  liz.addStreamInfo('video', { 'duration' : duration })
	#xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
  return ok
  
	
def geturl(url,data="x",header="",referer=""):
        global cj
        debug("Get Url: " +url)
        for cook in cj:
          debug(" Cookie :"+ str(cook))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))        
        userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
        if header=="":
          opener.addheaders = [('User-Agent', userAgent)]        
        else:
          opener.addheaders = header        
        if not referer=="":
           opener.addheaders = [('Referer', referer)]

        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             #debug( e.code )  
             cc=e.read()  
             debug("Error : " +cc)
             content=""
       
        opener.close()
        cj.save(cookie,ignore_discard=True, ignore_expires=True)               
        return content
		
def mUnescape(s):
	if '&' not in s:
		return s
	s = s.replace('&amp;','&')
	s = s.replace('&#034;','"')
	s = s.replace('&quot;','"')
	s = s.replace('&gt;','>')
	s = s.replace('&lt;','<')
	s = s.replace('&apos;',"'")
	s = s.replace('&commat;','@')
	s = s.replace('&percnt;','%')
	
	return s

def playvideo(url):
	reg_video='.*?<fileName>(.+?)<\/fileName>'
	reg_title='.*?<title>(.+?)<\/title>'
	reg_dur='.*?<duration>(.+?)<\/duration>'
	reg_desc='.*?<desc>(.+?)<\/desc>'
	reg_broad='.*?<broadcastDate>(.+?)<\/broadcastDate>'
	cont = geturl(url)
	content = smart_str(cont)
	#content = smart_str(testxml.xmlt())
	#print(content)
	title = re.search(reg_title,content).group(1)
	duration = re.search(reg_dur,content).group(1)
	desc = re.search(reg_desc,content).group(1)
	bdate = re.search(reg_broad,content).group(1)
	bdate = bdate[:bdate.find('T')].split('-')
	ndate = bdate[2]+"."+bdate[1]+"."+bdate[0]
	links = re.findall(reg_video,content,re.DOTALL)
	video = []
	for item in links:
		video.append(item)
	desc_full ='{} * vom {} * Dauer {}\n{}'.format(title, ndate, duration, desc)
	#print('{} \nSendung vom {}\nDauer {}\n{}'.format(title, ndate, duration, desc))	
	#print(video[1])
	#print(video[-1])
	try:
		listitem = xbmcgui.ListItem(path=video[-1])
	except:
		listitem = xbmcgui.ListItem(path=video[1])
	listitem.setInfo(type="Video", infoLabels={"Title": title, "Plot": desc_full, "Duration": duration})
	xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
	
def checkeins(url,m):
	#reg = 'mediaCon.*?<a href="(.+?)" class.*?mediaLink.*?\'m\':\{\'src\':\'(.+?)\'\}.*?headline.*?html.*?>(.+?)<'
	if url == '':
		url = "http://www.checkeins.de/videos/index.html"
	reg = 'mediaCon.*?<a href="(.+?)">.*?\'m\':\{\'src\':\'(.*?)\'\}.*?headline.*?html.*?>(.+?)<'
	regnext = '.*?<a.*?href="(.+?)">&gt;<\/a>|.*?<a.*?href="(.+?)">&lt;<\/a>'
	content = geturl(url)
	content = smart_str(content)
	#print(content)
	links = re.findall(reg,content,re.DOTALL)
	#print(links)
	start = 0
	if m == 'dir':
		start = 5
	for item in links[start:]:
		item = list(item)
		if str(item[1]).find('http') == -1:
			item[1] = main_url+str(item[1])
		if m == 'dir':
			item[0] = main_url+str(item[0][:item[0].find('"')])
			addDir(mUnescape(item[2]),item[0], "check1episode",item[1])
		if m == 'episodes':
			reg = '.*\/(.+)\.html'
			temp = re.search(reg,item[0])
			item[0] = main_url+'/'+temp.group(1)+'~playerXml.xml'
			addLink(mUnescape(item[2]),item[0], "playvideo",item[1])
	links = []
	if m == 'episodes':
		next = re.findall(regnext,content)
		# returns 2 tuple with 2 entries 1 ''
		if len(next) == 2:
			tprev = main_url+str(next[0][1])
			tnext = main_url+str(next[1][0])
			addDir('<<< prev', tprev, "check1episode",'')
			addDir('next >>>', tnext, "check1episode",'')
		if len(next) == 1:
			tnext = main_url+str(next[0][0])
			addDir('next >>>', tnext, "check1episode",'')
	xbmcplugin.endOfDirectory(addon_handle) 


params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
referer = urllib.unquote_plus(params.get('referer', ''))
page = urllib.unquote_plus(params.get('page', ''))
nosub= urllib.unquote_plus(params.get('nosub', ''))

     
if mode is '':
	checkeins('','dir')
else:
	if mode == 'Settings':
		addon.openSettings()
	if mode == 'playvideo':
		playvideo(url)
	if mode == 'check1episode':
		checkeins(url,'episodes')
	if mode == 'subrubrik':
		subrubrik(url)
		  
		  
		  
		  
		  
# Testarea #
'''
main_url = "http://www.checkeins.de"
#url = "http://www.checkeins.de/videos/index.html"
url = "http://www.checkeins.de/sendungen/die-checker/videos/index.html"
m='episodes'
checkeins(url,m)
url = 'http://www.checkeins.de/checker-can-der-biathlon-check-100~playerXml.xml'
playvideo(url)
#cProfile.run('liste()')
#cProfile.run("liste2()")
#checkeins()
print("################################")
'''


