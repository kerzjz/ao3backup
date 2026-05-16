import re
import sys
from pathlib import Path

# 👇 这行自动修复路径！万能！
sys.path.insert(0, str(Path(__file__).parent.parent))

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

# 👇 正确导入
from items import WorkItem


class WorkListSpider(CrawlSpider):
    name = "ao3"
    allowed_domains = ["archiveofourown.org"]
    start_urls = ["https://archiveofourown.org/users/ao3user/works"] # 👈 记得改成你自己的用户名

    rules = (
        Rule(LinkExtractor(allow=r'/works/\d+'), callback='parse_item'),
    )

    def parse_item(self, response):
        item = WorkItem()
        item['url'] = response.url
        item['title'] = response.xpath('//h2/text()').get()
        item['author'] = response.xpath('//a[@rel="author"]/text()').get()
        item['content'] = response.xpath('//div[@id="chapters"]').get()
        yield item
