from dataclasses import dataclass


@dataclass()
class RabbitConfig:

    host: str
    login: str
    password: str

