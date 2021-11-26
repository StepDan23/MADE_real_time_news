import logging
import scrapy
from scrapy.crawler import CrawlerProcess
from abc import abstractmethod


class NewsItem(scrapy.Item):
    title = scrapy.Field()
    text = scrapy.Field()


class NewsSpider(scrapy.Spider):
    custom_settings = {"FEEDS":
                           {"results.csv":
                                {"format": "csv",
                                 "fields": ["title", "text"],
                                 }
                            },
                       "LOG_LEVEL": logging.WARNING,
                       "DOWNLOAD_DELAY": 0.1,
                       }

    @abstractmethod
    def parse(self, response):
        pass

    @abstractmethod
    def parse_news(self, response):
        pass
