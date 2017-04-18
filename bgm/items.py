# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class DictField(scrapy.item.Field):
    def serializer(self, value):
        return ";".join(":".join([k, v]) for k, v in value.iteritems())

class Record(scrapy.Item):
    ## First five items are required.
    name = scrapy.Field()
    uid = scrapy.Field()
    typ = scrapy.Field()
    iid = scrapy.Field() #name and id together forms primary key.
    state = scrapy.Field()
    adddate = scrapy.Field()
    ## Following three are optional.
    rate = scrapy.Field()
    tags = scrapy.Field()

class Index(scrapy.Item):
    indexid = scrapy.Field()
    creator = scrapy.Field()
    favourite = scrapy.Field()
    date = scrapy.Field()
    items = scrapy.Field()

class Friend(scrapy.Item):
    """This item keeps a directed relationship that user is following his/her friend."""
    user = scrapy.Field()
    friend = scrapy.Field()
    # No date information

class Subject(scrapy.Item):
    subjectid = scrapy.Field()
    subjecttype = scrapy.Field()
    subjectname = scrapy.Field()
    order = scrapy.Field() # may be None
    # The following are all optional
    rank = scrapy.Field()
    votenum = scrapy.Field()
    favnum = scrapy.Field()
    date = scrapy.Field()

    #staff = scrapy.Field() # feature list!
    relations = scrapy.Field() #map
    relations['serializer'] = lambda x: u";".join(u":".join([k, v]) for k, v in x.iteritems())
    tags = scrapy.Field() #map
    tags['serializer'] = lambda x: u";".join(u":".join([k, unicode(v)]) for k, v in x.iteritems())
