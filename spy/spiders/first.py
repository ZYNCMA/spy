# coding=utf-8

from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import os
import sys
import MySQLdb
import memcache
import re

def get_id_douban(url):
    return url.split('/')[-2]

def get_id_tianya(url):
    uuu = url.split('/')[-1].split('-')
    uu = ""
    for i in range(len(uuu)-1):
        uu += uuu[i]+'-'
    return uu[:-1]

class first(BaseSpider):
    reload(sys)
    sys.setdefaultencoding('utf8')

    name = "first"
    allowed_domains = ["douban.com", "bbs.tianya.cn"]

    mc = memcache.Client(['127.0.0.1:11212'])

    start_urls = []

    def __init__(self, url=None, *args, **kwargs):
        if not url:
            print 'url none'
            sys.exit(1)

        douban = re.compile('^http://www.douban.com/group/topic/\d+/')
        tianya = re.compile('^http://bbs.tianya.cn/.+shtml$')
        if douban.match(url):
            tid = get_id_douban(url)
            self.start_urls = ["http://www.douban.com/group/topic/"+tid+"/?start=0"]
        elif tianya.match(url):
            tid = get_id_tianya(url)
            self.start_urls = ["http://bbs.tianya.cn/"+tid+"-1.shtml"]
        else:
            print 'url error'
            sys.exit(1)

        super(first, self).__init__(*args, **kwargs)

    def parse(self, response):
        if 'www.douban.com' in response.url:
            tid = get_id_douban(response.url)
            hxs = Selector(response)

            title = hxs.xpath("//div[@id='content']/h1/text()").extract()[0].strip()
            header = hxs.xpath('//div[@class="topic-content clearfix"]/div[@class="topic-doc"]')
            author = header.xpath('h3/span/a/text()').extract()[0]
            author_id = header.xpath("h3/span/a/@href").extract()[0].split('/')[-2]
            conn = MySQLdb.connect(
                host = 'localhost',
                port = 3306,
                user = 'root',
                passwd = 'root',
                db = 'db_thread_douban'
            )

        else:
            tid = get_id_tianya(response.url)
            hxs = Selector(response)

            title = hxs.xpath("//div[@id='post_head']/h1/span/span/text()").extract()[0].strip()
            div = hxs.xpath("//div[@id='post_head']/div")[0]
            author = div.xpath("div[@class='atl-info']/span/a/@uname").extract()[0]
            author_id = div.xpath("div[@class='atl-info']/span/a/@href").extract()[0].split('/')[-1]
            conn = MySQLdb.connect(
                host = 'localhost',
                port = 3306,
                user = 'root',
                passwd = 'root',
                db = 'db_thread_tianya'
            )

        cur = conn.cursor()
        cur.execute("insert into t_thread(tid, title, author, version, flag, author_id) values('%s', '%s', '%s', '0,0,1', '0,0', '%s')" % (tid, title, author, author_id))
        conn.commit()
        return []
