from typing import Generator
from requests import Session, get
from requests.exceptions import SSLError
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from re import findall
from pathlib import Path
from uuid import uuid4

from resources.api import Base_API
from resources.server_objects import User, Project, Repository, PullRequest
from resources.logger import log


class ServerSessionHandler(Base_API):
    def __init__(self, session: Session, base_url: str):
        self.session = session
        while base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.ssl_verify = self._validate_ssl(base_url)
        self.pagination_marker = 'isLastPage'
        self.pagination_page = 'start'
        self.pagination_per_page = 'limit'

    @staticmethod
    def _validate_ssl(base_url: str) -> bool:
        endpoint = f'{base_url}/status'
        try:
            r = get(endpoint)
            return True
        except SSLError:
            disable_warnings(InsecureRequestWarning)
            return False

    def download(self, endpoint: str, filename: str) -> Path:
        log.debug(f'Attempting to save attachment "{filename}" to {Path.cwd()}')
        _name, _extension = filename.split('.')
        _name_without_spaces = _name.replace(' ', '_')
        _uuid = uuid4()
        _name_with_hash = f'{_name_without_spaces}-{_uuid}'
        fs_filename = f'{_name_with_hash}.{_extension}'
        url = f'{self.base_url}{endpoint}'
        with open(fs_filename, 'wb') as local_file:
            r = self.session.get(url)
            local_file.write(r.content)

        return Path(fs_filename)


class Server(ServerSessionHandler):
    # https://developer.atlassian.com/server/bitbucket/reference/rest-api/

    def get_users(self) -> Generator[User, None, None]:
        '''
        GET /rest/api/latest/admin/users
        https://docs.atlassian.com/bitbucket-server/rest/7.18.0/bitbucket-rest.html#idp16
        '''
        endpoint = '/rest/api/1.0/admin/users'
        for value in self._get_paged_api(endpoint):
            user = User(value.get('slug'),
                        value.get('displayName'),
                        value.get('emailAddress'))
            log.info(f'Located user: {user}')
            yield user

    def get_projects(self) -> Generator[Project, None, None]:
        '''
        GET /rest/api/latest/projects
        https://docs.atlassian.com/bitbucket-server/rest/7.19.1/bitbucket-rest.html#idp149
        '''
        endpoint = "/rest/api/latest/projects"
        for value in self._get_paged_api(endpoint):
            project = Project(value.get('key'),
                              value.get('name'),
                              value.get('id'),
                              value.get('description'),
                              value.get('public'))
            yield project

    def get_repos(self, project: Project) -> Generator[Repository, None, None]:
        '''
        https://docs.atlassian.com/bitbucket-server/rest/7.21.0/bitbucket-rest.html#idp177
        '''
        endpoint = f'/rest/api/latest/projects/{project.key}/repos'
        for value in self._get_paged_api(endpoint):
            repo = Repository(value.get('slug'),
                              value.get('id'),
                              value.get('name'),
                              value.get('description'),
                              project=project)
            yield repo

    def get_pull_requests(self, project: Project, repo: Repository) -> Generator[PullRequest, None, None]:
        '''
        https://docs.atlassian.com/bitbucket-server/rest/7.21.0/bitbucket-rest.html#idp300
        '''
        endpoint = f'/rest/api/latest/projects/{project.key}/repos/{repo.slug}/pull-requests'
        for value in self._get_paged_api(endpoint):
            pr = PullRequest(value.get('id'),
                             value.get('title'),
                             value.get('description'),
                             value.get('state'),
                             value.get('createdDate'),
                             value.get('updatedDate'),
                             repo=repo)
            yield pr

    def get_pull_request_attachments(self, project: Project, repo: Repository, pr: PullRequest) -> Generator[dict, None, None]:
        '''
        https://docs.atlassian.com/bitbucket-server/rest/7.21.0/bitbucket-rest.html#idp331
        '''
        endpoint = f"/rest/api/latest/projects/{project.key}/repos/{repo.slug}/pull-requests/{pr.id}/activities"
        for value in self._get_paged_api(endpoint):
            if value.get('action') == "COMMENTED":
                if (comment := value.get('comment')):
                    comment: dict
                    if (text := comment.get('text')):
                        for attachment_id, filename in ServerUtils.strip_attachment_from_text(text):
                            yield attachment_id, filename

    def download_repo_attachment(self, project: Project, repo: Repository, attachment_id: int, filename: str) -> Path:
        '''
        https://docs.atlassian.com/bitbucket-server/rest/7.21.0/bitbucket-rest.html#idp206
        '''
        endpoint = f'/rest/api/latest/projects/{project.key}/repos/{repo.slug}/attachments/{attachment_id}'
        log.info(f'Attempting to download "{filename}" from server at URI "{endpoint}"')
        attachment = self.download(endpoint, filename)
        return attachment

class ServerUtils:
    @staticmethod
    def strip_attachment_from_text(text: str) -> Generator[tuple[int, str], None, None]:
        '''
        Example:
        in: "some text ![file.name](attachment:repo-id/attachment-id)"
        out: int(attachment-id), str(file.name)
        
        regex pattern: (\[(.*?)\]\(attachment:\d+\/\d+\))
        '''
        matches: list[list[str]] = findall(r'(\[(.*?)\]\(attachment:\d+\/\d+\))', text)
        for match in matches:
            attachment_id = int(match[0].split('/')[-1].strip(')'))
            filename = match[0].split(']')[0][1::]
            yield (attachment_id, filename)
