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
    cur.execute('select url, next from tianya')
    rsts = cur.fetchall()
    info = {}
    for rst in rsts:
        uid = get_id(rst[0])
        page = rst[1]
        info[uid] = {"next": page}
        url = "http://bbs.tianya.cn/"+uid+"-"+str(page)+".shtml"
        start_urls.append(url)

    def __init__(self, url=None, *args, **kwargs):
        if url:
            self.start_urls = [url]
            uid = get_id(url)
            self.info = {}
            self.info[uid] = {"next": 1}
        super(tianya, self).__init__(*args, **kwargs)

    def handle_last(self, response):
        return []

    def parse(self, response):
        uid = get_id(response.url)
        page = int(get_page(response.url))

        url = os.path.join("tianya", uid)
        if not os.path.exists(url):
            os.mkdir(url)
        f = open(os.path.join(url, str(page)), 'w')

        hxs = Selector(response)
        items = hxs.xpath('//div[@class="atl-item"]')
        for item in items:
            head = item.xpath('div[@class="atl-head"]/div[@class="atl-info"]').extract()
            body = item.xpath('div[@class="atl-content"]/div[contains(@class, "atl-con-bd")]/div[contains(@class, "bbs-content")]').extract()
            if head:
                f.write(head[0].strip())
            else:
                head = hxs.xpath('//div[@id="post_head"]/div[contains(@class, "atl-menu")]/div[@class="atl-info"]').extract()
                f.write(head[0].strip())
            f.write('\n')
            f.write(body[0].strip())
            f.write("\n\n")
        f.close()

        next_page = hxs.xpath('//div[@class="atl-pages"]/form/a[@class="js-keyboard-next"]/@href').extract()
        if next_page:
            return [self.make_requests_from_url("http://bbs.tianya.cn"+next_page[0])]
        else:
            return []
