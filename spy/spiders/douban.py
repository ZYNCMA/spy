from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import os
import sys
import MySQLdb

def get_id(url):
    return url.split('/')[-2]

def get_page(url):
    return url.split('=')[-1]

class douban(BaseSpider):
    reload(sys)
    sys.setdefaultencoding('utf8')

    conn= MySQLdb.connect(
        host='localhost',
        port = 3306,
        user='ya',
        passwd='mzy-ya',
        db ='devil',
    )
    cur = conn.cursor()

    name = "douban"
    allowed_domains = ["douban.com"]

    start_urls = []
    info = {}
    cur.execute('select uid, last, `update`, update_last, `total`, total_last, author from douban')
    rsts = cur.fetchall()
    for rst in rsts:
        url = "http://www.douban.com/group/topic/"+rst[0].strip()+"/?start="+str(rst[1])
        start_urls.append(url)

        uid = get_id(url)
        info[uid] = {"total": rst[4]-rst[5]}
        info[uid]["total_last"] = 0
        info[uid]["update"] = rst[2]-rst[3]
        info[uid]["update_last"] = 0
        info[uid]["author"] = rst[6]

    def __init__(self, url=None, *args, **kwargs):
        if url:
            self.start_urls = [url+"?start=0"]
        super(douban, self).__init__(*args, **kwargs)

    def handle_last(self, response):
        uid = get_id(response.url)
        page = get_page(response.url)
        hxs = Selector(response)

        if page == "0":
            self.info[uid]["total_last"] += 1
            self.info[uid]["update_last"] += 1

        reply = hxs.xpath('//ul[@class="topic-reply"]/li')
        for li in reply:
            href = li.xpath('div/a/@href')
            if href and href.extract()[0].split('/')[-2] == self.info[uid]["author"]:
                self.info[uid]["update_last"] += 1
            self.info[uid]["total_last"] += 1
        self.cur.execute('update douban set last=%d, `update`=%d, update_last=%d, `total`=%d, total_last=%d where uid=%s' %
                (int(page), self.info[uid]["update"], self.info[uid]["update_last"], self.info[uid]["total"], self.info[uid]["total_last"], uid))
        self.conn.commit()

    def parse(self, response):
        uid = get_id(response.url)
        page = get_page(response.url)
        hxs = Selector(response)
        next_page = hxs.xpath('//div[@class="paginator"]/span[@class="next"]/a/@href').extract()

        path = os.path.join("/home/ya/Desktop/douban", uid)
        if not os.path.exists(path):
            os.mkdir(path)
        f = open(os.path.join(path, page), 'w')

        if page == "0":
            topic = hxs.xpath('//div[@class="topic-content clearfix"]/div[@class="topic-doc"]')
            f.write(topic.xpath('h3').extract()[0].strip())
            f.write('\n')
            f.write(topic.xpath('div[@id="link-report"]/div[@class="topic-content"]').extract()[0].strip())
            f.write('\n')
            self.info[uid]["total"] += 1
            self.info[uid]["update"] += 1
        reply = hxs.xpath('//ul[@class="topic-reply"]')
        f.write(reply.extract()[0].strip())
        f.close()

        for li in reply.xpath('li'):
            href = li.xpath('div/a/@href')
            if href and href.extract()[0].split('/')[-2] == self.info[uid]["author"]:
                self.info[uid]["update"] += 1
            self.info[uid]["total"] += 1

        if next_page:
            return [self.make_requests_from_url(next_page[0])]
        else:
            self.handle_last(response)
            return []
