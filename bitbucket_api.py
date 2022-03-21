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
    for server_project in server.get_projects():
        for server_repo in server.get_repos(server_project):
            if not cloud.repo_exists(cloud.workspace, server_repo):
                log.info(f'Skipping repo "{server_repo.name}" as it is not present in your Cloud workspace')
                continue
            log.info(f'Scanning PRs from repo "{server_repo.name}"')
            for server_pr in server.get_pull_requests(server_project, server_repo):
                if not cloud.pr_exists(cloud.workspace, server_repo, server_pr.id):
                    log.info(f'Skipping pr "{server_pr.id}" from repo "{server_repo.name}" as is it not present in your Cloud workspace')
                    continue
                log.info(f'Scaning pr "{server_pr.id}" within repo "{server_repo.name}" for attachments')
                for attachment_id, filename in server.get_pull_request_attachments(server_project, server_repo, server_pr):
                    attachment = server.download_repo_attachment(server_project, server_repo, attachment_id, filename)
                    if cloud.upload_attachment_to_downloads(cloud.workspace, server_repo, attachment):
                        cloud.add_pr_comment(cloud.workspace, server_repo, server_pr.id, attachment)
                    else:
                        log.warning(f'Unable to upload {attachment} to {server_repo.name} under the download section')
                    remove_attachment_local_copy(attachment)

    log.info('Done. Closing...')
    exit()


if __name__ == '__main__':
    main()
