import functools
import requests

from datetime import datetime, timedelta
from contextlib import contextmanager

from boompy.errors import UnauthorizedError, InterfaceError, BoomiError
from boompy.resource import Resource
from boompy.base_api import API
from boompy import actions

__version__ = "0.0.1"

# The api instance all requests go through

class Boompy(object):

    def __init__(self, account_id, username, password):
        self.api = API(account_id, username, password)

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
            resource._api = self.api
            setattr(self, name, resource)

        class Account(Resource):
            _id_attr = "accountId"
            _uri = "Account"
            _name = "Account"
            _attributes = ("accountId", "name", "expirationDate", "status", "dateCreated")
            _api = self.api

            supported = {
                "get": True,
                "put": False,
                "post": True,
                "delete": False,
                "query": True,
            }

            def url(self, boomi_id=None):
                if getattr(self, self._id_attr) is None and boomi_id is None:
                    return "%s/%s" % (self.api.base_url(partner=True), self._uri)

                return super(Account, self).url(boomi_id=boomi_id)

        setattr(self, "Account", Account)

        class Role(Resource):
            _id_attr = "id"
            _uri = "Role"
            _name = "Role"
            _attributes = ("id", "parentId", "accountId", "name")

            supported = {
                "get": False,
                "put": False,
                "post": False,
                "query": False,
                "delete": False
            }

            @classmethod
            def query(cls, **kwargs):
                if kwargs:
                    raise InterfaceError("A keyword arg")

                return super(Role, cls).query()


    # Override the account_id value to pull info for partner accounts
    @contextmanager
    def sub_account(self, acct_id):
        old_boomi_id = self.api.partner_account
        self.api.partner_account = acct_id

        try:
            yield
        finally:
            self.api.partner_account = old_boomi_id


