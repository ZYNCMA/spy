# -*- coding: utf-8 -*-

# Scrapy settings for spy project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'spy'

SPIDER_MODULES = ['spy.spiders']
NEWSPIDER_MODULE = 'spy.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'spy (+http://www.yourdomain.com)'

DOWNLOAD_DELAY = 2
#LOG_FILE = "LOG"
