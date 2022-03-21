from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    slug: str
    display_name: str
    email: str

@dataclass
class Project:
    key: str
    name: str
    id: int
    description: str
    public: bool

@dataclass
class Repository:
    slug: str
    id: int
    name: str
    description: str
    project: Project

@dataclass
class PullRequest:
    id: int
    title: str
    description: str
    state: str
    created_date: datetime
    updated_date: datetime
    repo: Repository

    def __post_init__(self):
        #self.created_date = self.datetime_from_int(self.created_date)
        #self.updated_date = self.datetime_from_int(self.updated_date)
        ...

    @staticmethod
    def datetime_from_int(raw_time: int) -> datetime:
        #return datetime.fromtimestamp(raw_time)
        ...