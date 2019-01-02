#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcaddon, sys

import random
#import urllib.request
import urllib2
import json 
import datetime
import re

sendung = []
addon = xbmcaddon.Addon()
__setting__ = addon.getSetting
#
if __setting__('rbb') == 'true':
	sendung.append('Brandenburgaktuell')
	sendung.append('rbb')
if __setting__('ts') == 'true':
	sendung.append('tagesschau')
	sendung.append('ts')
if __setting__('ts24') == 'true':
	sendung.append('tagesschauXX')
	sendung.append('ts')
if __setting__('ht') == 'true':
	sendung.append('heute')
	sendung.append('ht')
if __setting__('hte') == 'true':
	sendung.append('heute-inEuropa')
	sendung.append('ht')
if __setting__('htd') == 'true':
	sendung.append('heute-inDeutschland')
	sendung.append('ht')
if __setting__('htp') == 'true':
	sendung.append('heuteplus')
	sendung.append('ht')
if __setting__('mdrh') == 'true':
	sendung.append('MDRSACHSEN-ANHALTHEUTE')
	sendung.append('mdrh')
if __setting__('htj') == 'true':
	sendung.append('heutejournal')
	sendung.append('ht')
if __setting__('sr') == 'true':
	sendung.append('Aktuell(XXUhr)')
	sendung.append('sr')
if __setting__('mdra') == 'true':
	sendung.append('MDRaktuellXX:XXUhr')
	sendung.append('mdrh')
if __setting__('ndra') == 'true':
	sendung.append('NDRAktuell')
	sendung.append('ndr')
if __setting__('srb') == 'true':
	sendung.append('aktuellerbericht')
	sendung.append('sr')
if __setting__('wdras') == 'true':
	sendung.append('AktuelleStunde')
	sendung.append('wdr')
if __setting__('swra') == 'true':
	sendung.append('SWRAktuellRheinland-Pfalz')
	sendung.append('swr')
if __setting__('hra') == 'true':
	sendung.append('hessenschau')
	sendung.append('hs')
if __setting__('brfa') == 'true':
	sendung.append('Frankenschauaktuell')
	sendung.append('brfa')

def datum(tim):
	return datetime.datetime.fromtimestamp(int(tim)).strftime('%d.%m.%Y')


def prep(str):
	prepstr = re.sub('\d', 'X', str)
	prepstr = prepstr.replace(' ','')
	prepstr = prepstr.replace('//','')
	if (prepstr == 'Aktuell(XX:XXUhr)'):
		prepstr = 'Aktuell(XXUhr)'
	if (prepstr=='heuteXX:XXUhr'):
		prepstr = 'heute'
	return prepstr

def start():
	size=200
	payload={'queries':[{'fields':['topic'],'query':'tagesschau'},{'fields':['topic'],'query':'heute'},{'fields':['topic'],'query':'Rundschau'},{'fields':['topic'],'query':'hessenschau'},{'fields':['topic'],'query':'aktuell'},{'fields':['channel'],'query':'zdf'},{'fields':['channel'],'query':'ard'}],'sortBy':'timestamp','sortOrder':'desc','future':False,'offset':0,'size':size}
	mvw = 'https://mediathekviewweb.de/api/query'
	#mvw = 'http://123derf.org/'
	params = json.dumps(payload).encode('utf8')
	req = urllib2.Request(mvw, data=params,headers={'content-type': 'text/plain'})
	try:
		response = urllib2.urlopen(req)
	except urllib2.HTTPError, e:
		notice('HTTPError = ' + str(e.code))
		xbmcgui.Dialog().notification('ERROR','mediathekviewweb.de nicht erreichbar',xbmcgui.NOTIFICATION_ERROR, 5000)
		return
	except urllib2.URLError, e:
		notice('URLError = ' + str(e.reason))
		xbmcgui.Dialog().notification('ERROR','mediathekviewweb.de nicht erreichbar',xbmcgui.NOTIFICATION_ERROR, 5000)
		return

	#sender = ['tagesschau','tagesschauXX','heute','heuteplus','RundschauNacht','heutejournal','NDR//Aktuell','SWRAktuellRheinland-Pfalz','Aktuell(XX:XXUhr)','SWRAktuellBaden-W\xc3rttemberg','MDRaktuellXX:XXUhr','Brandenburgaktuell','hessenschau','aktuellerbericht','MDRSACHSEN-ANHALTHEUTE','heuteXX:XXUhr','AktuelleStunde','Aktuell(XXUhr)','Leuteheute','Frankenschauaktuell','heute-inEuropa','heute-inDeutschland']
	#sender = ['tagesschau','tagesschauXX','heute','heuteplus','RundschauNacht','heutejournal','NDR//Aktuell','SWRAktuellRheinland-Pfalz','Aktuell(XX:XXUhr)','MDRaktuellXX:XXUhr','Brandenburgaktuell','hessenschau','aktuellerbericht','MDRSACHSEN-ANHALTHEUTE','heuteXX:XXUhr','AktuelleStunde','Aktuell(XXUhr)','Frankenschauaktuell','heute-inEuropa','heute-inDeutschland']
	


	j = json.loads(response.read())
	arr =  []
	hash = {}
	geb = u'Gebärden'.encode('utf-8')
	
	pl=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	pl.clear()

	for i in j['result']['results']:
		if(round((i['duration']/60))>9):
			topic = prep(i['topic'])
			if not topic in hash:
				if (not geb in topic.encode('utf-8')) and (not geb in i['title'].encode('utf-8')) and (topic in sendung): 
					up =  {topic:'x'}
					hash.update(up)
					date = datum(i['timestamp'])
					url = i['url_video_hd']
					if url == '':
						url = i['url_video']
					name = i['title']
					img = image(sendung[sendung.index(topic)+1])
					desc = i['description']
					if topic == 'Frankenschauaktuell':
						name = 'BR Frankenschau Aktuell'
					if topic == 'tagesschauXX':
						name = 'Tageschau 24'
						desc = i['title']
					if re.search('(31|30|[012]\d|\d)\.(0\d|1[012]|\d)\.(\d{1,6})',name) is None:
						name = name+' vom '+date 
					li = xbmcgui.ListItem(name,thumbnailImage=img)
					li.setInfo('video', { 'plot': desc })
					xbmc.PlayList(1).add(url,li)
					notice(topic)
					notice(url)
					
	
	xbmc.Player().play(pl)


def debug(content):
    log(content, xbmc.LOGDEBUG)

def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 


def mUnescape(s):
	if '&' not in s:
		return s
	s = s.replace('&amp;','&')
	s = s.replace('&quot;','"')
	s = s.replace('&gt;','>')
	s = s.replace('&lt;','<')
	s = s.replace('&apos;',"'")
	s = s.replace('&commat;','@')
	s = s.replace('&percnt;','%')
	return s

def image(sender):
	image = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')+'/resources/media/'+sender+'.png').decode('utf-8')
	return image

# START #
start()