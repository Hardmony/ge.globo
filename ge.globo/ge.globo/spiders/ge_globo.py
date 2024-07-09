import scrapy
from scrapy_splash import SplashRequest
from lxml import html
import json
from bs4 import BeautifulSoup

class GloboSpider(scrapy.Spider):
    name = "globo"
    allowed_domains = ['globo.com']
    data = []
    page = 1

    def get_new_list(self,page):
        return f'https://falkor-cda.bastian.globo.com/tenants/ge/instances/4ab5b6cd-f3e1-4be8-87c0-77bf6019d2a7/posts/page/{page}'

    def start_requests(self):
        yield scrapy.Request(self.get_new_list(self.page), self.parse)  #从第1页开始爬取

    def parse(self, response):
        res = json.loads(response.text)

        next_page = res['nextPage'] 

        for item in res['items']:
            detail_url = item['content']['url']
            yield scrapy.Request(detail_url, self.parse_link) #解析获取到的链接

        if next_page == 10: #这里通过判断时间
            return
        

        if next_page == self.page: # 下一页等于当前页就是爬完了
            print('end.')
            return
        else:
            self.page = next_page
            yield scrapy.Request(self.get_new_list(self.page), self.parse)


    def parse_link(self, response):
        print('parse')

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
