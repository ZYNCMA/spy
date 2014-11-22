from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import os
import sys
import MySQLdb
import memcache

def get_page(url):
    return url.split('.')[-2].split('-')[-1]

def get_id(url):
    uuu = url.split('/')[-1].split('-')
    uu = ""
    for i in range(len(uuu)-1):
        uu += uuu[i]+'-'
    return uu[:-1]

class tianya(BaseSpider):
    reload(sys)
    sys.setdefaultencoding('utf8')

    name = "tianya"
    allowed_domains = ["bbs.tianya.cn"]

    mc = memcache.Client(['127.0.0.1:11212'])

    conn= MySQLdb.connect(
        host='localhost',
        port = 3306,
        user='root',
        passwd='root',
        db ='db_thread_tianya',
    )
    cur = conn.cursor()

    start_urls = []
    cur.execute('select tid, version, flag, author_id from t_thread')
    rsts = cur.fetchall()
    info = {}
    for rst in rsts:
        version = rst[1].split(',')
        flag = rst[2].split(',')
        url = "http://bbs.tianya.cn/"+rst[0]+"-"+str(version[2])+".shtml"
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
            self.start_urls = ["http://bbs.tianya.cn/"+tid+"-1.shtml"]
            self.info = {}
            self.info[tid] = {}
            self.info[tid]['author_id'] = result[0]
            self.info[tid]['update'] = 0
            self.info[tid]['update_last'] = 0
            self.info[tid]['total'] = 0
            self.info[tid]['total_last'] = 0

        super(tianya, self).__init__(*args, **kwargs)

    def handle_last(self, response):
        tid = get_id(response.url)
        page = get_page(response.url)
        hxs = Selector(response)
        items = hxs.xpath('//div[@class="atl-item"]')
        for item in items:
            head = item.xpath('div[@class="atl-head"]/div[@class="atl-info"]')
            if not head:
                head = hxs.xpath('//div[@id="post_head"]/div[contains(@class, "atl-menu")]/div[@class="atl-info"]')
            if head.xpath('span/a/@href').extract()[0].split('/')[-1] == self.info[tid]["author_id"]:
                self.info[tid]["update_last"] += 1
            self.info[tid]["total_last"] += 1
        self.cur.execute('update tianya set last=%d, `update`=%d, update_last=%d, `total`=%d, total_last=%d where tid="%s"' %
                (int(page), self.info[tid]["update"], self.info[tid]["update_last"], self.info[tid]["total"], self.info[tid]["total_last"], tid))
        self.conn.commit()

    def parse(self, response):
        tid = get_id(response.url)
        page = get_page(response.url)

        path = os.path.join("/data/tianya", tid)
        if not os.path.exists(path):
            os.mkdir(path)
        f = open(os.path.join(path, page), 'w')

        hxs = Selector(response)
        items = hxs.xpath('//div[@class="atl-item"]')
        for item in items:
            head = item.xpath('div[@class="atl-head"]/div[@class="atl-info"]')
            body = item.xpath('div[@class="atl-content"]/div[contains(@class, "atl-con-bd")]/div[contains(@class, "bbs-content")]')
            if not head:
                head = hxs.xpath('//div[@id="post_head"]/div[contains(@class, "atl-menu")]/div[@class="atl-info"]')

            if head.xpath('span/a/@href').extract()[0].split('/')[-1] == self.info[tid]["author_id"]:
                self.info[tid]["update"] += 1
                f.write('<div class="t_author">\n')
            else:
                f.write('<div class="t_others">\n')
            f.write(head.extract()[0].strip())
            f.write('\n')
            f.write(body.extract()[0].strip())
            f.write('\n</div>\n\n')

            self.info[tid]["total"] += 1
        f.close()
        return []

        next_page = hxs.xpath('//div[@class="atl-pages"]/form/a[@class="js-keyboard-next"]/@href').extract()
        if next_page:
            return [self.make_requests_from_url("http://bbs.tianya.cn"+next_page[0])]
        else:
            self.handle_last(response)
            return []
