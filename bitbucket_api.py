from requests import Session
from pathlib import Path

from resources.cloud_api import Cloud
from resources import cloud_objects as CO
from resources.server_api import Server
from resources import server_objects as SO
from resources.logger import log

def init() -> tuple[Cloud, Server]:
    try:
        import env
        cloud_username = env.cloud_username
        cloud_password = env.cloud_password
        cloud_workspace = env.cloud_workspace

        server_username = env.server_username
        server_password = env.server_password
        server_url = env.server_url


    except [ImportError, NameError]:
        log.critical('The "env.py" file could not be found or one of the template variables is missing. '
                    'Please copy the "env_template.py" file to "env.py" and fill in your credentials '
                    'for either or both platforms before proceeding.')
        exit()
    cloud_session = Session()
    cloud_session.auth = (cloud_username, cloud_password)

    server_session = Session()
    server_session.auth = (server_username, server_password)

    cloud = Cloud(cloud_session, cloud_workspace)
    server = Server(server_session, server_url)
    return cloud, server

def remove_attachment_local_copy(attachment: Path):
    Path.unlink(attachment)

def main():
    cloud, server = init()
    for project in server.get_projects():
        for repo in server.get_repos(project):
            if not cloud.repo_exists(repo):
                continue
            for pr in server.get_pull_requests(project, repo):
                if not cloud.pr_exists(repo, pr):
                    continue
                for attachment_id, filename in server.get_pull_request_attachments(project, repo, pr):
                    attachment = server.download_repo_attachment(project, repo, attachment_id, filename)
                    cloud.upload_pr_attachment(attachment)
                    remove_attachment_local_copy(attachment)

    log.info('Done. Closing...')
    exit()


if __name__ == '__main__':
    main()
