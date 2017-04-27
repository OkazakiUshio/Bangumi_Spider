# -*- coding: utf-8 -*-

import scrapy
import re
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.http import Request
import datetime
from bgm.items import Record, Index, Friend, Subject
from bgm.util import *


class IndexSpider(scrapy.Spider):
    name='index'
    def __init__(self, *args, **kwargs):
        super(IndexSpider, self).__init__(*args, **kwargs)
        if not hasattr(self, 'id_max'):
            self.id_max=20000
        if not hasattr(self, 'id_min'):
            self.id_min=1
        self.start_urls = ["http://chii.in/index/"+str(i) for i in xrange(int(self.id_min),int(self.id_max))]

    def parse(self, response):
        if len(response.xpath(".//*[@id='columnSubjectBrowserA']/div[1]/a"))==0:
            return
        indexid = response.url.split('/')[-1]
        indexid=int(indexid)
        creator = response.xpath(".//*[@id='columnSubjectBrowserA']/div[1]/a/@href").extract()[0].split('/')[-1]
        creator=str(creator)
        td = response.xpath(".//*[@id='columnSubjectBrowserA']/div[1]/span/span[1]/text()").extract()[0]
        date = parsedate(td.split(' ')[0])
        if len(response.xpath(".//*[@id='columnSubjectBrowserA']/div[1]/span/span"))==2:
            favourite = response.xpath(".//*[@id='columnSubjectBrowserA']/div[1]/span/span[2]/text()").extract()[0]
            favourite = int(favourite)
        else: favourite = 0
        items = response.xpath(".//*[@id='columnSubjectBrowserA']/ul/li/@id").extract()
        items = [int(itm.split('_')[-1]) for itm in items]
        yield Index(indexid=indexid, creator=creator, favourite=favourite, date=date, items=items)

class RecordSpider(scrapy.Spider):
    name='record'
    def __init__(self, *args, **kwargs):
        super(RecordSpider, self).__init__(*args, **kwargs)
        if hasattr(self, 'type'):
            tplst = [itm.strip().lower() for itm in self.type.split(',')]
        else:
            tplst = ['anime', 'book', 'music', 'game', 'real']
        self.tplst = tplst
        if hasattr(self, 'userlist'):
            userlist = []
            with open(self.userlist, 'r') as fr:
                while True:
                    l = fr.readline().strip()
                    if not l: break;
                    userlist.append(l)
            self.start_urls = ["http://chii.in/user/{0}".format(i) for i in userlist]
        else:
            if not hasattr(self, 'id_max'):
                self.id_max=400000
            if not hasattr(self, 'id_min'):
                self.id_min=1
            self.start_urls = ["http://chii.in/user/{0}".format(i) for i in xrange(int(self.id_min),int(self.id_max))]

    def parse(self, response):
        username = response.url.split('/')[-1]
        try:
            nickname = response.xpath(".//h1[@class='nameSingle']/div[@class='inner']/a/text()").extract()[0].strip()
        except IndexError:
            nickname = u""
        if not 'redirect_urls' in response.meta:
            uid = int(username)
        else:
            uid = int(response.meta['redirect_urls'][0].split('/')[-1])

        if 'anime' in self.tplst and len(response.xpath(".//*[@id='anime']"))!=0:
            req = scrapy.Request("http://chii.in/anime/list/"+username, callback = self.merge)
            req.meta['uid']=uid
            req.meta['username']=username
            req.meta['nickname']=nickname
            yield req
        if 'game' in self.tplst and len(response.xpath(".//*[@id='game']"))!=0:
            req = scrapy.Request("http://chii.in/game/list/"+username, callback = self.merge)
            req.meta['uid']=uid
            req.meta['username']=username
            req.meta['nickname']=nickname
            yield req
        if 'book' in self.tplst and len(response.xpath(".//*[@id='book']"))!=0:
            req = scrapy.Request("http://chii.in/book/list/"+username, callback = self.merge)
            req.meta['uid']=uid
            req.meta['username']=username
            req.meta['nickname']=nickname
            yield req
        if 'music' in self.tplst and len(response.xpath(".//*[@id='music']"))!=0:
            req = scrapy.Request("http://chii.in/music/list/"+username, callback = self.merge)
            req.meta['uid']=uid
            req.meta['username']=username
            req.meta['nickname']=nickname
            yield req
        if 'real' in self.tplst and len(response.xpath(".//*[@id='real']"))!=0:
            req = scrapy.Request("http://chii.in/real/list/"+username, callback = self.merge)
            req.meta['uid']=uid
            req.meta['username']=username
            req.meta['nickname']=nickname
            yield req

    def merge(self, response):
        followlinks = response.xpath(".//div[@id='columnA']/div/div[1]/ul/li[2]//@href").extract() # a list of links
        for link in followlinks:
            req = scrapy.Request(u"http://chii.in"+link, callback = self.parse_recorder)
            req.meta['uid']=response.meta['uid']
            req.meta['username']=response.meta['username']
            req.meta['nickname']=response.meta['nickname']
            yield req

    def parse_recorder(self, response):
        state = response.url.split('/')[-1].split('?')[0]
        tp = response.url.split('/')[-4]

        items = response.xpath(".//*[@id='browserItemList']/li")
        for item in items:
            item_id = int(re.match(r"item_(\d+)",item.xpath("./@id").extract()[0]).group(1))
            item_date = parsedate(item.xpath("./div/p[@class='collectInfo']/span[@class='tip_j']/text()").extract()[0])
            if item.xpath("./div/p[@class='collectInfo']/span[@class='tip']"):
                item_tags = item.xpath("./div/p[@class='collectInfo']/span[@class='tip']/text()").extract()[0].split(u' ')[2:-1]
            else:
                item_tags=None

            try_match = re.match(r'sstars(\d+) starsinfo', item.xpath("./div/p[@class='collectInfo']/span[1]/@class").extract()[0])
            if try_match:
                item_rate = try_match.group(1)
                item_rate = int(item_rate)
            else:
                item_rate = None

            watchRecord = Record(nickname = response.meta['nickname'], name = response.meta['username'], uid = response.meta['uid'],
                typ = tp, state = state, iid = item_id, adddate = item_date)
            if item_tags:
                watchRecord["tags"]=item_tags
            if item_rate:
                watchRecord["rate"]=item_rate
            yield watchRecord

        if len(items)==24:
            request = scrapy.Request(getnextpage(response.url),callback = self.parse_recorder)
            request.meta['uid']=response.meta['uid']
            request.meta['username']=response.meta['username']
            request.meta['nickname']=response.meta['nickname']
            yield request


class FriendsSpider(scrapy.Spider):
    name='friends'
    handle_httpstatus_list = [302]
    def __init__(self, *args, **kwargs):
        super(FriendsSpider, self).__init__(*args, **kwargs)
        if not hasattr(self, 'id_max'):
            self.id_max=400000
        if not hasattr(self, 'id_min'):
            self.id_min=1
        self.start_urls = ["http://chii.in/user/"+str(i)+"/friends" for i in xrange(int(self.id_min),int(self.id_max))]

    def parse(self, response):
        user = response.url.split('/')[-2]
        lst = response.xpath(".//*[@id='memberUserList']/li//@href").extract()
        for itm in lst:
            yield Friend(user = user, friend = str(itm.split('/')[-1]))


class SubjectSpider(scrapy.Spider):
    name="subject"
    def __init__(self, *args, **kwargs):
        super(SubjectSpider, self).__init__(*args, **kwargs)
        if hasattr(self, 'itemlist'):
            itemlist = []
            with open(self.itemlist, 'r') as fr:
                while True:
                    l = fr.readline().strip()
                    if not l: break;
                    itemlist.append(l)
            self.start_urls = ["http://chii.in/subject/"+i for i in itemlist]
        else:
            if not hasattr(self, 'id_max'):
                self.id_max=200000
            if not hasattr(self, 'id_min'):
                self.id_min=1
            self.start_urls = ["http://chii.in/subject/"+str(i) for i in xrange(int(self.id_min),int(self.id_max))]

    def make_requests_from_url(self, url):
        rtn = Request(url)
        # rtn.meta['dont_redirect']=True
        return rtn;

    def parse(self, response):
        subjectid = int(response.url.split('/')[-1]) # trueid
        if not response.xpath(".//*[@id='headerSubject']"):
            return
        
        # This is used to filter those locked items
        # However, considering that current Bangumi ranking list does not exclude blocked items,
        # we include them in our spider.
        #if response.xpath(".//div[@class='tipIntro']"):
        #    return;

        if 'redirect_urls' in response.meta:
            order = int(response.meta['redirect_urls'][0].split('/')[-1])
        else:
            order = subjectid; # id

        subjecttype = response.xpath(".//div[@class='global_score']/div/small[1]/text()").extract()[0]
        subjecttype = subjecttype.split(' ')[1].lower();

        subjectname = response.xpath(".//*[@id='headerSubject']/h1/a/attribute::title").extract()[0]
        if not subjectname:
            subjectname = response.xpath(".//*[@id='headerSubject']/h1/a/text()").extract()[0]
        subjectname = subjectname.replace(u'\n', u' ')

        rank = response.xpath(".//div[@class='global_score']/div/small[2]/text()").extract()[0]
        if rank==u'--':
            rank=None;
        else:
            rank = int(rank[1:])
        votenum = int(response.xpath(".//*[@id='ChartWarpper']/div/small/span/text()").extract()[0])

        tplst = [itm.split('/')[-1] for itm in response.xpath(".//*[@id='columnSubjectHomeA']/div[3]/span/a/@href").extract()]
        favcount = [0]*5; j=1;
        for i in xrange(5):
            if not tplst or tplst[0]!=statestr[i]:
                favcount[i]=0;
            else:
                tmpstr = response.xpath(".//*[@id='columnSubjectHomeA']/div[3]/span/a["+str(j)+"]/text()").extract()[0]
                mtch = re.match(ur"^(\d+)", tmpstr);
                favcount[i] = int(mtch.group());
                j+=1
                tplst = tplst[1:]

        infokey = [itm[:-2] for itm in response.xpath(".//div[@class='infobox']//li/span/text()").extract()]
        infoval = response.xpath(".//div[@class='infobox']//li")
        infobox = dict()
        for key,val in zip(infokey, infoval):
            if val.xpath("a"):
                infobox[key]=[ref.split('/')[-1] for ref in
                      val.xpath("a/@href").extract()]

        date = None
        for datekey in datestr:
            if datekey in infokey:
                idx = infokey.index(datekey)
                try:
                    date = parsedate(infoval[idx].xpath('text()').extract()[0]) #may be none
                except:
                    date = None;
            if date is None:
                continue;
            else: break;

        relateditms = response.xpath(".//ul[@class='browserCoverMedium clearit']/li")
        relations = dict()
        for itm in relateditms:
            if itm.xpath("@class"):
                relationtype = itm.xpath("span/text()").extract()[0]
                relations[relationtype]=[itm.xpath("a[@class='title']/@href").
                                extract()[0].split('/')[-1]]
            else:
                relations[relationtype].append(itm.xpath("a[@class='title']/@href").
                                      extract()[0].split('/')[-1])
        brouche = response.xpath(".//ul[@class='browserCoverSmall clearit']/li")
        if brouche:
            relations[u'单行本']=[itm.split('/')[-1] for itm in
                           brouche.xpath("a/@href").extract()]


        yield Subject(subjectid=subjectid,
                      subjecttype=subjecttype,
                      subjectname=subjectname,
                      order=order,
                      rank=rank,
                      votenum=votenum,
                      favnum=';'.join([str(itm) for itm in favcount]),
                      date=date,
                      staff=infobox,
                      relations=relations)
