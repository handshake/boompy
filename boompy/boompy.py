import functools
import requests
import json

from requests.status_codes import codes as status_codes

from datetime import datetime, timedelta
from contextlib import contextmanager

from .errors import (
    APIRequestError,
    UnauthorizedError,
    InterfaceError,
    NotFoundError,
    RateLimitError,
    BoomiError
)

from .resource import Resource

BASE_URL = "https://api.boomi.com/api/rest/v1"
PARTNER_BASE_URL = "https://api.boomi.com/partner/api/rest/v1"

class Boompy(object):

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
        self.session = requests.session()
        init_resources_from_factory(self)
        init_resources_from_inheritance(self)

    # Override the account_id value to pull info for partner accounts
    @contextmanager
    def sub_account(self, acct_id):
        old_boomi_id = self.api.partner_account
        self.api.partner_account = acct_id

        try:
            yield
        finally:
            self.api.partner_account = old_boomi_id

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
        elif res.status_code in (status_codes.SERVICE_UNAVAILABLE, status_codes.TOO_MANY):
            raise RateLimitError(res)
        elif res.status_code == status_codes.NOT_FOUND:
            raise NotFoundError(res)
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

    def getAssignableRoles(self):
        results = []
        res = self.https_request("%s/getAssignableRoles" % self.base_url(), "get", {})

        for role in json.loads(res.content).get("Role"):
            results.append(boompy.Role(**role))

        return results


def init_resources_from_factory(boomi_object):
    entities = (
            ("AccountGroup", ("id", "defaultGroup", "name", "accountId"), {"delete": False}),
            ("AccountGroupAccount", ("id", "accountId", "accountGroupId"), {"put": False}),
            ("AccountUserRole", ("id", "accountId", "userId", "roleId", "notifyUser"), {"put": False}),
            ("Environment", ("id", "name", "classification"), {}),
            ("Events", ("eventId", "accountId", "atomId", "atomName", "eventLevel", "eventDate",
                        "status", "eventType", "executionId", "title", "startTime",
                        "errorDocumentCount", "inboundDocumentCount", "outboundDocumentCount",
                        "processName", "recordDate", "error", "environment", "classification",
                        "errorType", "erroredStepLabel", "erroredStepType"),
                {"put": False, "get": False, "delete": False, "post": False, "id_attr": "eventId"}),
            ("IntegrationPack", ("id", "name", "Description", "installationType"),
                {"put": False, "post": False, "delete": False}),
            ("IntegrationPackEnvironmentAttachment",
                ("id", "environmentId", "integrationPackInstanceId"), {"put": False, "get": False})
    )

    for name, attrs, kwargs in entities:
        resource = Resource.create_resource(name, attrs, **kwargs)
        resource.api = boomi_object
        setattr(boomi_object, name, resource)

def init_resources_from_inheritance(boomi_object):
    class Account(Resource):
        _id_attr = "accountId"
        _uri = "Account"
        _name = "Account"
        _attributes = ("accountId", "name", "expirationDate", "status", "dateCreated")
        _api = boomi_object

        supported = {
            "get": True,
            "put": False,
            "post": True,
            "delete": False,
            "query": True,
        }

        def url(self, boomi_id=None):
            if getattr(self, self._id_attr) is None and boomi_id is None:
                return "%s/%s" % (self._api.base_url(partner=True), self._uri)

            return super(Account, self).url(boomi_id=boomi_id)

    setattr(boomi_object, "Account", Account)

    class Role(Resource):
        _id_attr = "id"
        _uri = "Role"
        _name = "Role"
        _attributes = ("id", "parentId", "accountId", "name")
        _api = boomi_object

        supported = {
            "get": False,
            "put": False,
            "post": False,
            "query": True,
            "delete": False
        }

        @classmethod
        def query(cls, **kwargs):
            if kwargs:
                raise InterfaceError("A keyword arg")

            return super(Role, cls).query()

    setattr(boomi_object, "Role", Role)

