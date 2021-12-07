import os
import re
import json
import logging
from multiprocessing import Process, Queue
import scrapy
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from abc import abstractmethod


class NewsItem(scrapy.Item):
    text = scrapy.Field()


class NewsSpider(scrapy.Spider):
    custom_settings = {
        "LOG_LEVEL": logging.WARNING,
        "DOWNLOAD_DELAY": 0.1,
        "FEED_URI": "tmp.json",
        "FEED_FORMAT": "json",
    }

    @classmethod
    def set_url(cls, url):
        cls.start_urls = [url]

    @abstractmethod
    def parse(self, response):
        pass


class TassNewsSpider(NewsSpider):
    name = "TassNewsSpider"

    def parse(self, response):
        news_texts = response.css("div.text-block p ::text").extract()
        whole_text = "".join(news_texts)
        if not whole_text:
            return None
        news_item = NewsItem()
        news_item["text"] = re.sub("\xa0", " ", whole_text).strip()
        yield news_item


class LentaNewsSpider(NewsSpider):
    name = "LentaNewsSpider"

    def parse(self, response):
        news_texts = response.css(".b-text p ::text").extract()
        whole_text = "".join(news_texts)
        if not whole_text:
            return None
        news_item = NewsItem()
        news_item["text"] = re.sub("\xa0", " ", whole_text).strip()
        yield news_item


class RiaNewsSpider(NewsSpider):
    name = "RiaNewsSpider"

    def parse(self, response):
        news_texts = response.css("div.article__text ::text").extract()
        whole_text = "".join(news_texts[1:])
        if not whole_text:
            return None
        news_item = NewsItem()
        news_item["text"] = re.sub("\xa0", " ", whole_text).strip()
        yield news_item


class GazetaNewsSpider(NewsSpider):
    name = "GazetaNewsSpider"

    def parse(self, response):
        news_texts = response.css("div.b_article-text p ::text").extract()
        whole_text = "".join(news_texts)
        if not whole_text:
            return None
        news_item = NewsItem()
        news_item["text"] = re.sub("\xa0", " ", whole_text).strip()
        yield news_item


class MeduzaNewsSpider(NewsSpider):
    name = "MeduzaNewsSpider"

    def parse(self, response):
        news_texts = response.css("div.GeneralMaterial-article p ::text").extract()
        whole_text = "".join(news_texts[2:])
        if not whole_text:
            return None
        news_item = NewsItem()
        news_item["text"] = re.sub("\xa0", " ", whole_text).strip()
        yield news_item


def run_spider(spider):

    def crawl(queue):
        try:
            runner = CrawlerRunner({
                'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
            })
            deferred = runner.crawl(spider)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            queue.put(None)
        except Exception as e:
            queue.put(e)

    queue = Queue()
    process_crawl = Process(target=crawl, args=(queue, ))
    process_crawl.start()
    result = queue.get()
    process_crawl.join()

    if result is not None:
        raise result

    with open("tmp.json", "r") as read_file:
        data = json.load(read_file)[0]

    os.remove("tmp.json")
    return data["text"]
