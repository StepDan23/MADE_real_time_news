from pydantic import BaseModel


class RssConfig(BaseModel):
    """Конфигурация для считывания RSS ленты."""
    source_name: str
    rss_link: str
    timeout: int

