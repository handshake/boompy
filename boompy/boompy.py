import json

from contextlib import contextmanager

from .base_api import API
from .errors import InterfaceError
from .resource import Resource

class Boompy(object):

    def __init__(self, account_id, username, password):
        self._api = API(account_id, username, password)
        init_resources_from_factory(self)
        init_resources_from_inheritance(self)

    # Override the account_id value to pull info for partner accounts
    @contextmanager
    def sub_account(self, acct_id):
        old_boomi_id = self._api.partner_account
        self._api.partner_account = acct_id

        try:
            yield
        finally:
            self._api.partner_account = old_boomi_id

    def getAssignableRoles(self):
        results = []
        res = self.https_request("%s/getAssignableRoles" % self.api._base_url(), "get", {})

        for role in json.loads(res.content).get("Role"):
            results.append(self.Role(**role))

        return results


def init_resources_from_factory(boomi_object):
    entities = (
            ("AccountGroup", ("id", "defaultGroup", "name", "accountId"), {"delete": False}),
            ("AccountGroupAccount", ("id", "accountId", "accountGroupId"), {"put": False}),
            ("AccountUserRole", ("id", "accountId", "userId", "roleId", "notifyUser"), {"put": False}),
            ("Environment", ("id", "name", "classification"), {}),
            ("Event", ("eventId", "accountId", "atomId", "atomName", "eventLevel", "eventDate",
                        "status", "eventType", "executionId", "title", "startTime",
                        "errorDocumentCount", "inboundDocumentCount", "outboundDocumentCount",
                        "processName", "recordDate", "error", "environment", "classification",
                        "errorType", "erroredStepLabel", "erroredStepType"),
                {"put": False, "get": False, "delete": False, "post": False, "id_attr": "eventId"}),
            ("IntegrationPack", ("id", "name", "Description", "installationType"),
                {"put": False, "post": False, "delete": False}),
            ("IntegrationPackInstance", ("id", "integrationPackOverrideName", "integrationPackId"),
                {"put": False, "get": True, "query": True, "post": True, "delete": True}),
            ("IntegrationPackEnvironmentAttachment",
                ("id", "environmentId", "integrationPackInstanceId"), {"put": False, "get": False})
    )

    for name, attrs, kwargs in entities:
        resource = Resource.create_resource(name, attrs, **kwargs)
        resource._api = boomi_object._api
        setattr(boomi_object, name, resource)

def init_resources_from_inheritance(boomi_object):
    class Account(Resource):
        _id_attr = "accountId"
        _uri = "Account"
        _name = "Account"
        _attributes = ("accountId", "name", "expirationDate", "status", "dateCreated")
        _api = boomi_object._api

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

