import json
import requests

from requests.status_codes import codes as status_codes

import boompy

from boompy.errors import APIRequestError, BoomiError, UnauthorizedError

BASE_URL = "https://api.boomi.com/api/rest/v1"
PARTNER_BASE_URL = "https://api.boomi.com/partner/api/rest/v1"

class API(object):

    account_id = None
    username = None
    password = None
    session = None
    partner_account = None

    def __init__(self, account_id, username, password):
        self.account_id = account_id
        self.username = username
        self.password = password
        self.session = requests.session()

        if self.username is None:
            raise UnauthorizedError("Boomi username not provied")

        if self.password is None:
            raise UnauthorizedError("Boomi username not provied")

        if self.account_id is None:
            raise UnauthorizedError("Boomi account id not provied")


    def https_request(self, url, method, data):
        if self.partner_account:
            url = "%s?overrideAccount=%s" % (url, self.partner_account)

        session = self.session_with_headers()
        fn = getattr(session, method)
        try:
            res = fn(url, data=json.dumps(data))
        except Exception, e:
            raise BoomiError(e)

        if res.status_code == status_codes.OK:
            return res
        else:
            raise APIRequestError(res)


    def base_url(self, partner=False):
        return "%s/%s" % (PARTNER_BASE_URL if (partner or self.partner_account)  else BASE_URL, self.account_id)

    def session_with_headers(self):
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        return self.session

