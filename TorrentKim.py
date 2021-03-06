﻿#-*- coding: utf-8 -*-
#! /usr/bin/python

#import grequests
import os
import requests
import BeautifulSoup
import telepot
import urllib2
import sqlite3
import hashlib
import traceback

from LogManager import log

from urllib import quote,unquote
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from operator import itemgetter

import main



class TorrentKim(object):
    """description of class"""

    db_path = main.botConfig.GetExecutePath() + "/cbbot.db"


    def __init__(self):
        # DB fail if not exists - Create DB
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()

        query = """CREATE TABLE IF NOT EXISTS "TG_CB" (
	                `ID`	TEXT NOT NULL,
	                `TYPE`	INTEGER NOT NULL,
	                `VALUE`	TEXT NOT NULL,
	                PRIMARY KEY(ID)
                );"""

        log.info('TorKim Query : %s', query)
        cursor.execute(query)
        db.commit()

        cursor.close()
        db.close()
        
            
    
    def SearchTorrentKim(self, keyword, type=1, max_count=10, page_count = 2):

        if type < 1 or type > 2:
            log.info('Search Torrent Kim, Unknown Type:%d', type)
            return False, None

        tor_url = 'https://torrentkim3.net/bbs/s.php?k='

        urlTest = tor_url + quote(keyword.encode('utf-8'))
        
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11')]
        data = opener.open(urlTest)
        
        sp = BeautifulSoup.BeautifulSoup(data)
        
        pageList = self.GetPageLink(sp, page_count)
        
        titleList = self.GetTitle(sp)
        if titleList == None:
            log.info("%s not found torrent", keyword)
            return False, None
        
        for page in pageList:
            data = opener.open(page)
            sp = BeautifulSoup.BeautifulSoup(data)
            titleList.update(self.GetTitle(sp, len(titleList)))
        
        sortTorList = sorted(titleList.items(), reverse=True)

        inline_keyboard = self.MakeTorrentInlineKeyboard(sortTorList, type, max_count)

        return True, inline_keyboard

        

    def GetTitle(self, bs, start_idx = 0):
        torTable = bs.find('table', attrs={'class':'board_list'})

        if torTable == None:
            log.info("Not Found Torrent")
            return None
    
        torTRs = torTable.findAll('tr', attrs={'class':'bg1'})
    
        idx = start_idx
    
        titleList = dict()
        listValue = list()
    
        sortRatingList = list()
    
        
        for item in torTRs:
            Rating = item.find('font').text
            TargetItem = item.find('a', attrs={'target':'s'})
            if TargetItem == None:
                continue
            Title = TargetItem.text
            torUrl = 'https://torrentkim3.net' + item.find('a', attrs={'target':'s'})['href'][2:]
    
            titleList[torUrl] = list()
            
            titleList[torUrl].append(Rating)
            titleList[torUrl].append(Title)
    
            idx = idx + 1
    
        return titleList
    
    
    def GetPageLink(self, bs, page_count=2):
        baseUrl = 'https://torrentkim3.net/bbs/s.php'
        pageDiv = bs.find('div', attrs={'class':'board_page'})
        pageLinks = pageDiv.findAll('a')

        count = 0
    
        pageLinkList = list()
    
        for item in pageLinks:
            if count >= page_count:
                break

            pageLinkList.append(baseUrl + item['href'])
            count = count + 1
    
        return pageLinkList


    
    def GetTorrentFileLink(self, bbsUrl):
        try:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11')]
            data = opener.open(bbsUrl)
            sp = BeautifulSoup.BeautifulSoup(data)
        
            ATags = sp.findAll('a', {'rel' : 'nofollow'})
            fullLink = ATags[1]['href']

            start = fullLink.find("'")+1
            end = fullLink.find("'", start)
    
            fileLink = 'https://torrentkim3.net' + fullLink[start:end]

            torrentName = sp.find('div', {'id': 'writeContents'}).find('legend').text
        except urllib2.HTTPError, e:
            log.error("GetTorrentFileLink Fail, HTTPError:'%d', Except :'%s'", e.code, e)
            return '', ''
        except urllib2.URLError, e:
            log.error("GetTorrentFileLink Fail, URLError:'%s', Except :'%s'", str(e.reason), e)
            return '', ''
        except httplib.HTTPException, e:
            log.error("GetTorrentFileLink Fail, HTTP Exception :'%s'", str(e.reason), e)
            return '', ''
    
        return fileLink, torrentName
    
    
    def GetTorrentFile(self, bbsUrl):
        try:
            torrentUrl, torrentName = self.GetTorrentFileLink(bbsUrl)
            if torrentUrl == '' or torrentName == '':
                log.error("GetTorrentFile| GetTorrentFileLink Fail")
                return False, ''

            #torrentName = "/tmp/" + torrentName
            torrentName = os.path.join(u"/tmp/", torrentName)

            r = requests.get(torrentUrl, stream=True, headers={'referer': bbsUrl})
    
            size = float(r.headers['content-length']) / 1024.0
    
            with open(torrentName.encode('utf-8'), 'wb') as f: 
                chunks = enumerate(r.iter_content(chunk_size=1024)) 
                for index, chunk in chunks: 
                    if chunk: 
                        f.write(chunk) 
                        f.flush() 
        except requests.exceptions.RequestException as e: 
            log.error('GetTorrentFile Fail, Request Exception : %s', e)
            log.error("GetTorrentfile Exception : %s", traceback.format_exc())
            return False, ''
        except:
            log.error("Get Torrent File Fail, url:'%s'", bbsUrl)
            log.error("GetTorrentfile Exception : %s", traceback.format_exc())
            return False, ''

        return True, torrentName.encode('utf-8')
    
    
    
    def MakeTorrentInlineKeyboard(self, torList, type=1, max_count=10):
        # sqlite ID, Type, Value
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()

        inline_keyboard_list = list()
        idx = 0
    
        for item in torList:
            if idx >= max_count:
                break
    
            # 고유키는 Url 링크를 SHA-1 으로 처리 한 값으로 한다.
            unique_id = hashlib.sha1(item[0].encode('utf-8')+str(type)).hexdigest()
            query = "INSERT OR REPLACE INTO TG_CB VALUES('%s', %d, '%s');" % (unique_id, type, item[0])
            log.info('TorKim Query : %s', query)
            cursor.execute(query)

            if type == 1:
                itemText = '[' + item[1][0] + '] ' + item[1][1]
            elif type == 2:
                itemText = 'DOWNLOAD:[' + item[1][0] + '] ' + item[1][1]
                
            callbackText = "%s" % (unique_id)
    
            tempList = list()
            tempList.append(InlineKeyboardButton(text=itemText, callback_data=callbackText))
            inline_keyboard_list.append(tempList)
    
            idx = idx + 1

        db.commit()

        cursor.close()
        db.close()
    
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard_list)



