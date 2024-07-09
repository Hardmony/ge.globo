import scrapy
from scrapy_splash import SplashRequest
from lxml import html
import json
from bs4 import BeautifulSoup

class FtbSpider(scrapy.Spider):
    name = "globo"
    allowed_domains = ['ge.globo.com']
    start_urls = ['https://ge.globo.com/futebol/']
    data = []

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, args={'wait': 3})  # Increase wait time to allow JS to load

    def parse(self, response):
        
        # 使用 lxml 解析 HTML
        tree = html.fromstring(response.text)
        
        # 提取标题中的文章链接
        article_links = tree.xpath('//div[@class="_evt"]/h2/a/@href')

        # 遍历每一个链接，发送请求并调用 parse_link 进行解析
        for link in article_links:
            yield SplashRequest(link, self.parse_link, args={'wait': 3})

    def parse_link(self, response):
        # 使用 lxml 解析 HTML
        tree = html.fromstring(response.text)

        # 提取title
        title = tree.xpath('//h1[@class="content-head__title" and @itemprop="headline"]/text()')

        # 提取keywords
        keywords = tree.xpath('//meta[@name="keywords"]/@content')
        keywords = keywords[0].strip() if keywords else None

        # 提取description
        description = tree.xpath('//h2[@class="content-head__subtitle" and @ itemprop="alternativeHeadline"]/text()')
        description = ' '.join([desc.strip() for desc in description]) if description else None


        # 提取content  具有特定类和属性的内容
        content_second = tree.xpath('//p[@class=" content-text__container " and @ data-track-category="Link no Texto" and @ data-track-links=""]')
        content_two = ''.join([
            BeautifulSoup(html.tostring(part), 'lxml').get_text().strip() for part in content_second
            if not part.xpath('.//strong')
        ])

        content_first = tree.xpath('//p[@class=" content-text__container theme-color-primary-first-letter " and @ data-track-category="Link no Texto" and @ data-track-links=""]')
        content_one = ''
        if content_first:
            content_one = ''.join([
                BeautifulSoup(html.tostring(part), 'lxml').get_text().strip() for part in content_first
                if not part.xpath('.//strong')
            ])
            content = content_one + content_two
        else:
            content = content_two


        if title:
            title = title[0].strip()
            # self.logger.info(f'Title: {title}')
            self.data.append({
                'title' : title ,
                'keywords' : keywords ,
                'description': description ,
                'content' : content ,
                'url' : response.url ,
                })

    def close(self, reason):
        # 将数据保存成 JSON 文件
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
