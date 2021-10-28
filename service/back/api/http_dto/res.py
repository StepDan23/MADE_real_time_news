"""
Server response template
"""
from pydantic import BaseModel


class ResponseOut(BaseModel):
    news: dict