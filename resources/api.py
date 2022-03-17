from requests import Session, Response
from typing import Generator
from time import sleep
from sys import exit

from resources.logger import log

class Base_API:
    '''
    Do not Instantiate this class directly.
    Instead, create a resources.cloud_api.Cloud() or
    resources.server_api.Server() class as they inherit
    from this base class.
    '''

    def __init__(self) -> None:
        self.session: Session = None
        self.base_url: str = None
        self.ssl_verify: bool = None
        self.pagination_marker: str = None
        self.pagination_page: str = None
        self.pagination_per_page: str = None

    def _get_api(self, endpoint: str, params: dict=None, headers: dict=None) -> dict:
        endpoint = self._validate_endpoint(endpoint)
        url = f'{self.base_url}{endpoint}'

        r = self.session.get(url, params=params, headers=headers, verify=self.ssl_verify)
        return r.json()

    def _get_paged_api(self, endpoint: str, params: dict=None, headers: dict=None,
                       page: int=None) -> Generator[dict, None, None]:
        endpoint = self._validate_endpoint(endpoint)
        url = f'{self.base_url}{endpoint}'

        while True:
            if params is None:
                params = {self.pagination_page: page, self.pagination_per_page: 100}
            elif isinstance(params, dict):
                # Persist whatever params are passed in, only overwriting/appending page specifically
                params[self.pagination_page] = page

            r = self.session.get(url, params=params, headers=headers, verify=self.ssl_verify)

            if not self._api_rate_limited(r.status_code) and self._authorized(r.status_code):
                r_json = r.json()
                for value in r_json.get('values'):
                    yield value
            
            # not 'next' cloud, 'isLastPage' server
            if self.base_url == 'https://api.bitbucket.org':
                next_page_present = r.json().get(self.pagination_marker)
            else:
                # TODO verify isLastPage always exists for server responses
                next_page_present = not r.json().get(self.pagination_marker)
            page = self._page_handler(page, next_page_present)

            if page is None:
                # Breaks out of while True when the last page's content has already been yielded
                return

    def _put_api(self, endpoint: str, params: dict=None, headers: dict=None, 
                 json: dict=None, data: dict=None) -> Response:
        endpoint = self._validate_endpoint(endpoint)
        url = f'{self.base_url}{endpoint}'

        while True:
            r = self.session.put(url, params=params, headers=headers, json=json,
                                 data=data, verify=self.ssl_verify)

            if not self._api_rate_limited(r.status_code) and self._authorized(r.status_code):
                return r

    def _post_api(self, endpoint: str, params: dict=None, headers: dict=None,
                  json: dict=None, data: dict=None) -> Response:
        endpoint = self._validate_endpoint(endpoint)
        url = f'{self.base_url}{endpoint}'

        while True:
            r = self.session.post(url, params=params, headers=headers, json=json,
                                  data=data, verify=self.ssl_verify)

            if not self._api_rate_limited(r.status_code) and self._authorized(r.status_code):
                return r

    def _delete_api(self, endpoint: str, params: dict=None, headers: dict=None) -> Response:
        endpoint = self._validate_endpoint(endpoint)
        url = f'{self.base_url}{endpoint}'

        while True:
            r = self.session.delete(url, params=params, headers=headers, verify=self.ssl_verify)

            if not self._api_rate_limited(r.status_code) and self._authorized(r.status_code):
                return r

    @staticmethod
    def _validate_endpoint(endpoint) -> str:
        # Prepends a forward slash if not present
        if endpoint[0] != "/":
            endpoint = f'/{endpoint}'
        return endpoint

    @staticmethod
    def _api_rate_limited(status_code: int) -> bool:
        if status_code == 429:
            log.info('Hit api rate limit, sleeping for 1 minute then attempting to resume...')
            sleep(60)
            return True
        return False

    @staticmethod
    def _authorized(status_code: int) -> bool:
        if status_code == 401:
            log.critical('Received 401 response indicating misspelled/invalid credentials, '
                         'please check your credentials and try again. Closing...')
            exit()
        elif status_code == 403:
            log.critical('Received 403 response indicating missing permissions, '
                         'please ensure you have granted yourself site admin and try again. '
                         'Closing...')
            exit()
        return True

    @staticmethod
    def _page_handler(next_page: int, next_page_present: bool):
        if not next_page_present:
            return None

        if next_page is None:
            next_page = 1
        next_page = next_page + 1

        return next_page
