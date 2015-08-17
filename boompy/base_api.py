import requests
import json

from requests.status_codes import codes as status_codes

from .errors import (
    APIRequestError,
    UnauthorizedError,
    NotFoundError,
    RateLimitError,
    BoomiError
)

BASE_URL = "https://api.boomi.com/api/rest/v1"
PARTNER_BASE_URL = "https://api.boomi.com/partner/api/rest/v1"

class API(object):
    account_id = None
    username = None
    password = None
    session = None
    partner_account = None

    def __init__(self, account_id, username, password):
        if username is None:
            raise UnauthorizedError("Boomi username not provied")

        if password is None:
            raise UnauthorizedError("Boomi username not provied")

        if account_id is None:
            raise UnauthorizedError("Boomi account id not provied")

        self.account_id = account_id
        self.username = username
        self.password = password
        self.session = self._session_with_headers()

    def https_request(self, url, method, data):
        if self.partner_account:
            url = "%s?overrideAccount=%s" % (url, self.partner_account)

        fn = getattr(self.session, method)
        try:
            res = fn(url, data=json.dumps(data))
        except Exception, e:
            raise BoomiError(e)

        if res.status_code == status_codes.OK:
            return res
        elif res.status_code in (status_codes.SERVICE_UNAVAILABLE, status_codes.TOO_MANY):
            raise RateLimitError(res)
        elif res.status_code == status_codes.NOT_FOUND:
            raise NotFoundError(res)
        else:
            raise APIRequestError(res)


    def base_url(self, partner=False):
        return "%s/%s" % (PARTNER_BASE_URL if (partner or self.partner_account)  else BASE_URL, self.account_id)

    def _session_with_headers(self):
        session = requests.session()
        session.auth = (self.username, self.password)
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        return session


