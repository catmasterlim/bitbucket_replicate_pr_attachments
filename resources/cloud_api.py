from pathlib import Path
from resources.api import Base_API
from resources.logger import log
from typing import Generator, Iterable, Tuple
from resources.cloud_objects import Workspace, User, Group, Repository, Project
from requests import Session


class CloudSessionHandler(Base_API):
    def __init__(self, session: Session, workspace: str):
        self.session = session
        self.workspace = workspace
        self.base_url = 'https://api.bitbucket.org'
        self.ssl_verify = True
        self.pagination_marker = 'next'
        self.pagination_page = 'page'
        self.pagination_per_page = 'pagelen'


class Cloud(CloudSessionHandler):
    # Rest 2.0 https://developer.atlassian.com/cloud/bitbucket/rest/intro/
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.workspace is not None:
            self.workspace = self.get_workspace(self.workspace)
        else:
            self.workspace = self.choose_workspace()

    def choose_workspace(self) -> Workspace:
        workspace = None
        log.info('Select a workspace to work on...')
        log.info('select the number of the cooresponding workspace and press enter. '
                 'If desired workspace is not present, leave blank and press enter.')
        available_workspaces = [workspace for workspace in self.get_available_workspaces()]
        _workspace_batch, _counter = [], 0
        for num, workspace in enumerate(available_workspaces):
            _workspace_batch.append({'id': num, 'workspace': workspace})
            _counter += 1
            if _counter > 5:
                formatted_workspaces = [f"[{x.get('id')}] {x.get('workspace')}" for x in _workspace_batch]
                print(', '.join(formatted_workspaces))
                selection = input('Select number or leave blank: ')
                if selection != "":
                    workspace = [x.get('workspace') for x in _workspace_batch if x.get('id') == selection][0]
                    break
                _workspace_batch, _counter = [], 0
        if workspace is None:
            log.fatal('No Bitbucket Cloud workspace was selected. Cannot continue, Exiting...')
            exit()
        return workspace

    # Workspaces https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/
    def get_available_workspaces(self, filters: str=None) -> Generator[Workspace, None, None]:
        '''
        GET /2.0/workspaces
        '''
        endpoint = '/2.0/workspaces'
        params = {'q': filters}

        for value in self._get_paged_api(endpoint, params=params):
            workspace = Workspace(value.get('uuid'),
                                  value.get('slug'),
                                  value.get('name'))
            log.info(f'Located workspace: {workspace}')
            yield workspace

    def get_workspace(self, workspace_id: str) -> Workspace:
        '''
        GET /2.0/workspaces/{workspace}

        If passing in a uuid instead of slug, pre-formate with %7B and %7D
        '''
        endpoint = f'/2.0/workspaces/{workspace_id}'
        json = self._get_api(endpoint)
        workspace = Workspace(json.get('uuid'),
                              json.get('slug'),
                              json.get('name'))
        return workspace

    def create_workspace(self, workspace_name: str):
        '''
        
        '''
        ...

    def get_all_workspace_repository_permissions(self, workspace: Workspace) -> Iterable[Tuple[User, str, Repository]]:
        '''
        GET /2.0/workspaces/{workspace}/permissions/repositories

        https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/#api-workspaces-workspace-permissions-repositories-get
        '''
        endpoint = f'/2.0/workspaces/{workspace.slug}/permissions/repositories'
        
        for value in self._get_paged_api(endpoint):
            user = User(value.get('user').get('display_name'),
                        value.get('user').get('uuid'))
            permission = value.get('permission')
            repository = Repository(value.get('repository').get('name'),
                                    value.get('repository').get('full_name'),
                                    value.get('repository').get('uuid'))
            yield user, permission, repository

    def get_workspace_repositories(self, workspace: Workspace) -> Generator[Repository, None, None]:
        '''
        GET /2.0/repositories/{workspace}
        '''
        endpoint = f'/2.0/repositories/{workspace.slug}'
        
        for value in self._get_paged_api(endpoint):
            repository = Repository(value.get('name'),
                                    value.get('full_name'),
                                    value.get('uuid'),
                                    value.get('is_private'),
                                    value.get('project').get('name'),
                                    value.get('project').get('key'))
            log.info(f'Located repository: {repository.full_details}')
            yield repository

    def get_workspace_projects(self, workspace: Workspace) -> Generator[Project, None, None]:
        # https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/#api-workspaces-workspace-projects-project-key-get
        '''
        GET /2.0/workspaces/{workspace}/projects
        '''
        endpoint = f'/2.0/workspaces/{workspace.slug}/projects'
        for value in self._get_paged_api(endpoint):
            project = Project(value.get('uuid'),
                              value.get('is_private'),
                              value.get('key'),
                              value.get('name'),
                              value.get('has_publicly_visible_repos'))
            log.info(f'Located Project: {project.full_details}')
            yield project

    def repo_exists(self, workspace: Workspace, repo: Repository) -> bool:
        '''
        GET /2.0/repositories/{workspace}/{repo}

        https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/#api-repositories-workspace-repo-slug-get
        '''
        endpoint = f'/2.0/repositories/{workspace.slug}/{repo.slug}'
        r_json = self._get_api(endpoint)
        if r_json.get('error'):
            return False
        return True

    def pr_exists(self, workspace: Workspace, repo: Repository, pr_id: int) -> bool:
        '''
        GET /2.0/repositories/{workspace}/{repo}/pullrequests/{pull_request}

        https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-pull-request-id-get
        '''
        endpoint = f'/2.0/repositories/{workspace.slug}/{repo.slug}/pullrequests/{pr_id}'
        r_json = self._get_api(endpoint)
        if r_json.get('error'):
            return False
        return True

    def add_pr_comment(self, workspace: Workspace, repo: Repository, pr_id: int, attachment=Path) -> bool:
        '''
        returns True if successful, else False
        POST /2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/comments

        https://developer.atlassian.com/cloud/bitbucket/rest/api-group-pullrequests/#api-repositories-workspace-repo-slug-pullrequests-pull-request-id-comments-post
        '''
        headers = {'Content-type': 'application/json'}
        endpoint = f'/2.0/repositories/{workspace.slug}/{repo.slug}/pullrequests/{pr_id}/comments'
        file_url = f'https://bitbucket.org/{workspace.slug}/{repo.slug}/downloads/{attachment}'
        message = f'[{attachment}]({file_url})'
        payload = {'content': {'raw': message}}
        r = self._post_api(endpoint, json=payload, headers=headers)
        r_json: dict = r.json()
        if r.status_code != 201 or r_json.get('error'):
            log.debug(f'Failed to create comment on pr "{pr_id}" in repo "{repo.slug}" with message:\n{message}\nStatus_code: {r.status_code}\nText: {r.text}')
            return False
        log.debug(f'Successfully added comment on pr "{pr_id}" in repo "repo.slug" for "{attachment}"')
        return True

    def upload_attachment_to_downloads(self, workspace: Workspace, repo: Repository, attachment: Path) -> bool:
        '''
        POST /2.0/repositories/{workspace}/{repo_slug}/downloads

        https://developer.atlassian.com/cloud/bitbucket/rest/api-group-downloads/?utm_source=%2Fbitbucket%2Fapi%2F2%2Freference%2Fresource%2Frepositories%2F%257Bworkspace%257D%2F%257Brepo_slug%257D%2Fdownloads&utm_medium=302#post
        '''
        endpoint = f'/2.0/repositories/{workspace.slug}/{repo.slug}/downloads'
        #headers = {'Content-type': 'multipart/form-data', 'Accept': 'appliction/json'}
        headers = {}
        with open(attachment, 'rb') as byte_file:
            files = {'files': byte_file}
            r = self._post_api(endpoint, headers=headers, files=files)
        if r.status_code == 201:
            log.debug(f'Successfully uploaded "{attachment}" to repo "{repo.name}"')
            return True
        log.debug(f'Failed to upload "{attachment}" for repo "{repo.name}" due to the following error:\n\t{r.status_code}\n\t{r.text}')
        return False
