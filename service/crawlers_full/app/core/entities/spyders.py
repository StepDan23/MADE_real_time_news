import re

from news import NewsItem, NewsSpider


class TassNewsSpider(NewsSpider):
    name = "TassNewsSpider"
    url_base = "https://tass.ru"
    start_urls = ["https://tass.ru/"]

    def parse(self, response):
        for link in response.css("a.news-preview ::attr(href)").extract():
            yield response.follow(self.url_base + link, callback=self.parse_news)

    def parse_news(self, response):
        title = response.css("h1.news-header__title ::text").get()
        response.css("span explainer__title ::text").get()
        news_texts = response.css("div.text-block p ::text").extract()
        whole_text = "".join(news_texts)
        if not (title and whole_text):
            return None
        news_item = NewsItem()
        news_item["title"] = re.sub("\xa0", " ", title)
        news_item["text"] = re.sub("\xa0", " ", whole_text)
        yield news_item


class LentaNewsSpider(NewsSpider):
    name = "LentaNewsSpider"
    url_base = "https://lenta.ru"
    start_urls = ["https://lenta.ru/parts/news/"]

    def parse(self, response):
        for link in response.css('div.item.news h3 a::attr(href)').extract():
            if link[:5] == "/news":
                yield response.follow(self.url_base + link, callback=self.parse_news)

    def parse_news(self, response):
        title = response.css("h1::text").get()
        news_texts = response.css(".b-text p ::text").extract()
        whole_text = "".join(news_texts)
        if not (title and whole_text):
            return None
        news_item = NewsItem()
        news_item["title"] = re.sub("\xa0", " ", title)
        news_item["text"] = re.sub("\xa0", " ", whole_text)
        yield news_item


class RiaNewsSpider(NewsSpider):
    name = "RiaNewsSpider"
    url_base = "https://ria.ru/"
    start_urls = ["https://ria.ru/"]

    def parse(self, response):
        for link in response.css('div.lenta__item a ::attr(href)'):
            try:
                yield response.follow(link, callback=self.parse_news)
            except:
                return None

    def parse_news(self, response):
        title = response.css("div.article__title::text").get()
        news_texts = response.css("div.article__text ::text").extract()
        whole_text = "".join(news_texts[1:])
        if not (title and whole_text):
            return None
        news_item = NewsItem()
        news_item["title"] = re.sub("\xa0", " ", title)
        news_item["text"] = re.sub("\xa0", " ", whole_text)
        yield news_item


class GazetaNewsSpider(NewsSpider):
    name = "GazetaNewsSpider"
    url_base = "https://www.gazeta.ru"
    start_urls = ["https://www.gazeta.ru/"]

    def parse(self, response):
        for link in response.css("div.b_ear-textblock a::attr(href)").extract():
            if link.startswith("/"):
                yield response.follow(self.url_base + link, callback=self.parse_news)

    def parse_news(self, response):
        titles_all = response.css("div.b_article-header")
        h1 = titles_all.css("h1 ::text").get()
        h2 = titles_all.css("h2 ::text").get()
        title = h1 if h1 else h2
        news_texts = response.css("div.b_article-text p ::text").extract()
        whole_text = "".join(news_texts)
        if not (title and whole_text):
            return None
        news_item = NewsItem()
        news_item["title"] = re.sub("\xa0", " ", title)
        news_item["text"] = re.sub("\xa0", " ", whole_text)
        yield news_item


class MeduzaNewsSpider(NewsSpider):
    name = "MeduzaNewsSpider"
    url_base = "https://meduza.io"
    start_urls = ["https://meduza.io/"]

    def parse(self, response):
        for link in response.css("h2 a ::attr(href)").extract():
            yield response.follow(self.url_base + link, callback=self.parse_news)

    def parse_news(self, response):

        title = response.css("h1 ::text").get()
        news_texts = response.css("div.GeneralMaterial-article p ::text").extract()
        whole_text = "".join(news_texts[2:])
        if not (title and whole_text):
            return None
        news_item = NewsItem()
        news_item["title"] = re.sub("\xa0", " ", title)
        news_item["text"] = re.sub("\xa0", " ", whole_text)
        yield news_item
