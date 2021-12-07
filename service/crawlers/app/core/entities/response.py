from pydantic import BaseModel
from scrapy import Spider


class RssConfig(BaseModel):
    """Конфигурация для считывания RSS ленты."""
    source_name: str
    rss_link: str
    timeout: int
    spider: Spider

