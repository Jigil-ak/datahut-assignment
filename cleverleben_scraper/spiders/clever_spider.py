import scrapy


class CleverSpiderSpider(scrapy.Spider):
    name = "clever_spider"
    allowed_domains = ["cleverleben.at"]
    start_urls = ["https://cleverleben.at"]

    def parse(self, response):
        pass
