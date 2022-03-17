from dataclasses import dataclass, field

@dataclass
class UUID:
    '''
    raw = ID only
    payload = ID wrapped in curly brackets
    url_formatted = ID wrapped in "%7B" and "%7D" respectively
    '''
    payload: str

    def __post_init__(self) -> None:
        if not self.payload[0] == '{':
            self.payload = '{' + self.payload
        if not self.payload[-1] == '}':
            self.payload = self.payload + '}'
        self.raw = self.payload.replace('{', '').replace('}', '')
        self.url_formatted = f'%7B{self.raw}%7D'
    
    def __str__(self) -> str:
        return self.payload

@dataclass
class Workspace:
    uuid: UUID
    slug: str
    name: str

    def __post_init__(self) -> None:
        self.uuid = UUID(self.uuid)

    def __str__(self) -> str:
        return f'UUID: {self.uuid} | Slug: {self.slug} | Name: {self.name}'

@dataclass
class User:
    display_name: str
    uuid: UUID

    def __post_init__(self) -> None:
        self.uuid = UUID(self.uuid)
    
    def __str__(self) -> str:
        return f'UUID: {self.uuid} | Display Name: {self.display_name}'

@dataclass
class Group:
    ...

@dataclass
class Repository:
    name: str
    full_name: str
    uuid: UUID
    is_private: bool
    project_name: str
    project_key: str
    members: list = field(default_factory=lambda: [])
    slug: str = None

    @property
    def full_details(self) -> None:
        return f'UUID: {self.uuid} | Full Name: {self.full_name} | Is Private: {self.is_private} | Project Name: {self.project_name} | Project Key: {self.project_key}'

    def __post_init__(self):
        self.uuid = UUID(self.uuid)
        self.slug = self.full_name.split('/')[1]

    def __str__(self) -> str:
        return f'UUID: {self.uuid} | Full Name: {self.full_name}'

    def add_member(self, member: User) -> None:
        self.members.append(member)

@dataclass
class Project:
    uuid: UUID
    is_private: bool
    key: str
    name: str
    has_publicly_visible_repos: bool

    def __post_init__(self) -> None:
        self.uuid = UUID(self.uuid)

    @property
    def full_details(self) -> None:
        return f'UUID: {self.uuid} | Key: {self.key} | Name: {self.name} | Is Private: {self.is_private} | Contains Public Repos: {self.has_publicly_visible_repos}'
