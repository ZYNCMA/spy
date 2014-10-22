from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import os
import sys
import MySQLdb

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
    cur.execute('select url from douban')
    urls = cur.fetchall()
    for url in urls:
        url = url[0].strip()+"?start=0"
        start_urls.append(url)

    def __init__(self, url=None, *args, **kwargs):
        if url:
            self.start_urls = [url+"?start=0"]
        super(douban, self).__init__(*args, **kwargs)

    def handle_last(self, response):
        return []

    def parse(self, response):
        url = response.url.split('=')
        page = url[1]
        url = url[0].split('/')[-2]
        hxs = Selector(response)
        next_page = hxs.xpath('//div[@class="paginator"]/span[@class="next"]/a/@href').extract()

        url = os.path.join("douban", url)
        if not os.path.exists(url):
            os.mkdir(url)
        f = open(os.path.join(url, page), 'w')

        if page == "0":
            topic = hxs.xpath('//div[@class="topic-content clearfix"]/div[@class="topic-doc"]')
            f.write(topic.xpath('h3').extract()[0].strip())
            f.write('\n')
            f.write(topic.xpath('div[@id="link-report"]/div[@class="topic-content"]').extract()[0].strip())
            f.write('\n')
        reply = hxs.xpath('//ul[@class="topic-reply"]').extract()
        f.write(reply[0].strip())
        f.close()

        if next_page:
            return [self.make_requests_from_url(next_page[0])]
        else:
            self.handle_last(response)
            return []
