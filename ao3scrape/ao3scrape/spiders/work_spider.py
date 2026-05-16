""" Spider that combs ALL stories on AO3. """
import re
import scrapy
from urllib.parse import urlparse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from ao3scrape.items import WorkItem


class WorkListSpider(CrawlSpider):
    name = "ao3"
    allowed_domains = ["archiveofourown.org"]

    # 从 AO3 最新作品列表开始爬全站
    start_urls = [
        "https://archiveofourown.org/works?utf8=✓&sort_by=updated"
    ]

    rules = [
        # 提取作品链接，自动拼接完整阅读参数
        Rule(
            LinkExtractor(
                allow=r'^/works/\d+$',
                deny=(r'bookmarks', r'comments', r'collections', r'tags', r'users')
            ),
            callback='parse_item',
            follow=False
        ),
        # 自动翻页
        Rule(
            LinkExtractor(allow=r'\?page=\d+', restrict_xpaths='//a[@rel="next"]'),
            follow=True
        )
    ]

    # 给链接添加成人内容 + 全文阅读参数
    def _process_request(self, request):
        request.url += "?view_adult=true&view_full_work=true"
        return request

    def strip_and_join(self, list_text, separator=" "):
        text = separator.join(list_text).strip()
        stripped_text = re.sub("<.*?>", "", text)
        return stripped_text

    def parse_tags(self, response, item, tag_category):
        xpath = f'//dd[@class="{tag_category} tags"]/ul/li/a/text()'
        item[tag_category] = response.xpath(xpath).getall()

    def parse_item(self, response):
        item = WorkItem()
        parsed_url = urlparse(response.url)
        item['work_id'] = re.search(r'/works/(\d+)', parsed_url.path).group(1)
        item['title'] = response.xpath('//h2/text()').get('').strip()
        item['author'] = response.xpath('//h3[@class="byline heading"]/a[@rel="author"]/text()').getall()
        item['published'] = response.xpath('//dd[@class="published"]/text()').get('').strip()
        item['summary'] = ''.join(response.xpath('//div[@class="preface group"]/div[@class="summary module"]/blockquote/*').getall()).strip()
        item['notes'] = ''.join(response.xpath('//div[@class="preface group"]/div[@class="notes module"]/blockquote/*').getall()).strip()

        for category in ["rating", "warning", "category", "fandom", "relationship", "character", "freeform"]:
            self.parse_tags(response, item, category)

        item['language'] = response.xpath('//dd[@class="language"]/text()').get('').strip()

        if response.xpath('//dd[@class="series"]'):
            item['series'] = response.xpath('//dd[@class="series"]/span/span/a/text()').getall()
            position_text = response.xpath('//span[@class="position"]/text()').get()
            if position_text:
                pos = re.search(r'Part (\d+) of', position_text)
                item['series_position'] = pos.group(1) if pos else ''

        if response.xpath('//div[@class="chapter"]'):
            item['multi_chapter_text'] = response.xpath('//div[@id="chapters"]/*').getall()
        else:
            item['single_chapter_text'] = "".join(response.xpath('//div[@id="chapters"]/div[@class="userstuff"]/*').getall()).strip()

        yield item
