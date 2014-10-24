from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import os
import sys
import MySQLdb

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

    conn= MySQLdb.connect(
        host='localhost',
        port = 3306,
        user='ya',
        passwd='mzy-ya',
        db ='devil',
    )
    cur = conn.cursor()

    name = "tianya"
    allowed_domains = ["bbs.tianya.cn"]

    start_urls = []
    cur.execute('select uid, last, `update`, update_last, `total`, total_last, author from tianya')
    rsts = cur.fetchall()
    info = {}
    for rst in rsts:
        url = "http://bbs.tianya.cn/"+rst[0]+"-"+str(rst[1])+".shtml"
        start_urls.append(url)

        uid = get_id(url)
        info[uid] = {"total": rst[4]-rst[5]}
        info[uid]["total_last"] = 0
        info[uid]["update"] = rst[2]-rst[3]
        info[uid]["update_last"] = 0
        info[uid]["author"] = rst[6]

    def __init__(self, url=None, *args, **kwargs):
        if url:
            self.start_urls = [url]
            uid = get_id(url)
            self.info = {}
            self.info[uid] = {"next": 1}
        super(tianya, self).__init__(*args, **kwargs)

    def handle_last(self, response):
        uid = get_id(response.url)
        page = get_page(response.url)
        hxs = Selector(response)
        items = hxs.xpath('//div[@class="atl-item"]')
        for item in items:
            head = item.xpath('div[@class="atl-head"]/div[@class="atl-info"]')
            if not head:
                head = hxs.xpath('//div[@id="post_head"]/div[contains(@class, "atl-menu")]/div[@class="atl-info"]')
            if head.xpath('span/a/@href').extract()[0].split('/')[-1] == self.info[uid]["author"]:
                self.info[uid]["update_last"] += 1
            self.info[uid]["total_last"] += 1
        self.cur.execute('update tianya set last=%d, `update`=%d, update_last=%d, `total`=%d, total_last=%d where uid="%s"' %
                (int(page), self.info[uid]["update"], self.info[uid]["update_last"], self.info[uid]["total"], self.info[uid]["total_last"], uid))
        self.conn.commit()

    def parse(self, response):
        uid = get_id(response.url)
        page = int(get_page(response.url))

        path = os.path.join("/home/ya/Desktop/tianya", uid)
        if not os.path.exists(path):
            os.mkdir(path)
        f = open(os.path.join(path, str(page)), 'w')

        hxs = Selector(response)
        items = hxs.xpath('//div[@class="atl-item"]')
        for item in items:
            head = item.xpath('div[@class="atl-head"]/div[@class="atl-info"]')
            body = item.xpath('div[@class="atl-content"]/div[contains(@class, "atl-con-bd")]/div[contains(@class, "bbs-content")]')
            if head:
                f.write(head.extract()[0].strip())
            else:
                head = hxs.xpath('//div[@id="post_head"]/div[contains(@class, "atl-menu")]/div[@class="atl-info"]')
                f.write(head.extract()[0].strip())
            f.write('\n')
            f.write(body.extract()[0].strip())
            f.write("\n\n")
            if head.xpath('span/a/@href').extract()[0].split('/')[-1] == self.info[uid]["author"]:
                self.info[uid]["update"] += 1
            self.info[uid]["total"] += 1
        f.close()

        next_page = hxs.xpath('//div[@class="atl-pages"]/form/a[@class="js-keyboard-next"]/@href').extract()
        if next_page:
            return [self.make_requests_from_url("http://bbs.tianya.cn"+next_page[0])]
        else:
            self.handle_last(response)
            return []
