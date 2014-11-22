from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import os
import sys
import MySQLdb
import memcache

def get_id(url):
    return url.split('/')[-2]

def get_page(url):
    return url.split('=')[-1]

class douban(BaseSpider):
    reload(sys)
    sys.setdefaultencoding('utf8')

    name = "douban"
    allowed_domains = ["douban.com"]

    mc = memcache.Client(['127.0.0.1:11212'])

    conn= MySQLdb.connect(
        host='localhost',
        port = 3306,
        user='root',
        passwd='root',
        db ='db_thread_douban',
    )
    cur = conn.cursor()

    start_urls = []
    info = {}
    cur.execute('select tid, version, flag, author_id from t_thread')
    rsts = cur.fetchall()
    for rst in rsts:
        version = rst[1].split(',')
        flag = rst[2].split(',')
        url = "http://www.douban.com/group/topic/"+rst[0].strip()+"/?start="+str(version[2])
        start_urls.append(url)

        tid = rst[0]
        info[tid] = {"total": int(version[0])-int(flag[0])}
        info[tid]["total_last"] = 0
        info[tid]["update"] = int(version[1])-int(flag[1])
        info[tid]["update_last"] = 0
        info[tid]["author_id"] = rst[3]

    def __init__(self, url=None, *args, **kwargs):
        if url:
            tid = get_id(url)
            self.cur.execute('select author_id from t_thread where tid="%s"' % tid)
            result = self.cur.fetchall()[0]
            self.start_urls = ["http://www.douban.com/group/topic/"+tid+"/?start=0"]
            self.info = {}
            self.info[tid] = {}
            self.info[tid]['author_id'] = result[0]
            self.info[tid]['update'] = 0
            self.info[tid]['update_last'] = 0
            self.info[tid]['total'] = 0
            self.info[tid]['total_last'] = 0

        super(douban, self).__init__(*args, **kwargs)

    def handle_last(self, response):
        tid = get_id(response.url)
        page = get_page(response.url)
        hxs = Selector(response)

        if page == "0":
            self.info[tid]["total_last"] += 1
            self.info[tid]["update_last"] += 1

        reply = hxs.xpath('//ul[@class="topic-reply"]/li')
        for li in reply:
            href = li.xpath('div/a/@href')
            if href and href.extract()[0].split('/')[-2] == self.info[tid]["author_id"]:
                self.info[tid]["update_last"] += 1
            self.info[tid]["total_last"] += 1
        self.cur.execute('update t_thread set last=%d, `update`=%d, update_last=%d, `total`=%d, total_last=%d where tid=%s' %
                (int(page), self.info[tid]["update"], self.info[tid]["update_last"], self.info[tid]["total"], self.info[tid]["total_last"], tid))
        self.conn.commit()

    def parse(self, response):
        tid = get_id(response.url)
        page = get_page(response.url)
        hxs = Selector(response)
        next_page = hxs.xpath('//div[@class="paginator"]/span[@class="next"]/a/@href').extract()

        path = os.path.join("/data/douban", tid)
        if not os.path.exists(path):
            os.mkdir(path)
        f = open(os.path.join(path, page), 'w')

        if page == "0":
            topic = hxs.xpath('//div[@class="topic-content clearfix"]/div[@class="topic-doc"]')
            f.write('<div class="t_author">')
            f.write(topic.xpath('h3').extract()[0].strip())
            f.write('\n')
            f.write(topic.xpath('div[@id="link-report"]/div[@class="topic-content"]').extract()[0].strip())
            f.write('</div>\n\n')
            self.info[tid]["total"] += 1
            self.info[tid]["update"] += 1

        reply = hxs.xpath('//ul[@class="topic-reply"]')
        for li in reply.xpath('li'):
            href = li.xpath('div/a/@href')
            if href and href.extract()[0].split('/')[-2] == self.info[tid]["author_id"]:
                self.info[tid]["update"] += 1
                f.write('<div class="t_author">\n'+li.extract()+'\n</div>\n\n')
            else:
                f.write('<div class="t_others">\n'+li.extract()+'\n</div>\n\n')
            self.info[tid]["total"] += 1
        f.close()
        return []

        if next_page:
            return [self.make_requests_from_url(next_page[0])]
        else:
            self.handle_last(response)
            return []
