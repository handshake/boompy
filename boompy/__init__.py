from contextlib import contextmanager

from .base_api import API
from .errors import InterfaceError, APIRequestError, BoomiError
from .resource import Resource
from . import actions

__version__ = "0.0.4"

__all__ = ["Account", "Role"]

def set_auth(account_id, username, password):
    """ Sets the auth on the API singleton. """
    API()._set_auth(account_id, username, password)

# Override the account_id value to pull info for partner accounts
@contextmanager
def sub_account(acct_id):
    """ Used for accessing a sub account while persisting youre current api credentials. """
    api = API()
    old_boomi_id = api.partner_account
    api.partner_account = acct_id

    try:
        yield
    finally:
        api.partner_account = old_boomi_id

class Account(Resource):
    _id_attr = "accountId"
    _uri = "Account"
    _name = "Account"
    _attributes = ("accountId", "name", "expirationDate", "status", "dateCreated")

    supported = {
        "get": True,
        "put": False,
        "post": True,
        "delete": False,
        "query": True,
    }

    # Override the base Resource.url because of some partner stuff while creating an account
    def url(self, boomi_id=None):
        if getattr(self, self._id_attr) is None and boomi_id is None:
            return "%s/%s" % (API().base_url(partner=True), self._uri)
        return super(Account, self).url(boomi_id=boomi_id)

class Role(Resource):
    _id_attr = "id"
    _uri = "Role"
    _name = "Role"
    _attributes = ("id", "parentId", "accountId", "name")

    supported = {
        "get": False,
        "put": False,
        "post": False,
        "query": True,
        "delete": False
    }

    # Override the base Resource.query because you cant actually query Role on its attributes.
    @classmethod
    def query(cls, **kwargs):
        if kwargs:
            raise InterfaceError("A keyword arg")
        return super(Role, cls).query()


class AccountUserRole(Resource):
    _id_attr = "id"
    _uri = "AccountUserRole"
    _name = "AccountUserRole"
    _attributes = ("id", "accountId", "userId", "roleId", "notifyUser")

    supported = {
        "get": False,
        "put": False,
        "post": True,
        "query": True,
        "delete": True,
    }

    # Override the base Resource.query because boomi returns a 500 error instead of a 404 for the
    # AccountUserRole resource... wat
    @classmethod
    def query(cls, **kwargs):
        try:
            super(AccountUserRole, cls).query(**kwargs)
        except APIRequestError:
            return []

entities = (
        ("AccountGroup", ("id", "defaultGroup", "name", "accountId"), {"delete": False}),
        ("AccountGroupAccount", ("id", "accountId", "accountGroupId"), {"put": False}),
        ("Atom", ("instanceId", "currentVersion", "dateInstalled", "hostName", "type", "status",
                  "name", "id", "cloudId"), {}),
        ("AtomExtensions", ("id", "extensionGroupId", "atomId"), {"post": False, "delete": False}),
        ("AtomMapExtension", ("name", "mapId", "processId", "id", "extensionGroupId", "atomId"),
            {"query": False, "post": False, "delete": False}),
        ("AtomMapExtensionsSummary", ("name", "mapId", "processId", "id", "extensionGroupId",
                                      "atomId", "DestinationFieldSet", "SourceFieldSet"),
            {"get": False, "post": False, "put": False, "delete": False}),
        ("Deployment", ("id", "digest", "environmentId", "processId"),
            {"put": False, "delete": False}),
        ("Environment", ("id", "name", "classification"), {}),
        ("EnvironmentAtomAttachment", ("atomId", "environmentId", "id"),
            {"get": False, "put": False}),
        ("EnvironmentExtensions",
            ("id", "extensionGroupId", "environmentId", "processProperties", "connections"),
            {"post": False, "delete": False}),
        ("EnvironmentMapExtension",
            ("name", "mapId", "processId", "id", "extensionGroupId", "environmentId"),
            {"query": False, "post": False, "delete": False}),
        ("EnvironmentMapExtensionsSummary",
            ("name", "mapId", "processId", "id", "extensionGroupId", "environmentId",
                "DestinationFieldSet", "SourceFieldSet"),
            {"get": False, "post": False, "put": False, "delete": False}),
        ("Event", ("eventId", "accountId", "atomId", "atomName", "eventLevel", "eventDate",
                    "status", "eventType", "executionId", "title", "startTime", "endTime",
                    "errorDocumentCount", "inboundDocumentCount", "outboundDocumentCount",
                    "processName", "recordDate", "error", "environment", "classification",
                    "errorType", "erroredStepLabel", "erroredStepType"),
            {"put": False, "get": False, "delete": False, "post": False, "id_attr": "eventId"}),
        ("InstallerToken", ("id", "installType", "durationMinutes", "cloudId", "token", "expiration", "created", "accountId"),
            {"query": False, "put": False, "get": False, "delete": False, "post": True}),
        ("IntegrationPack", ("id", "name", "Description", "installationType"),
            {"put": False, "post": False, "delete": False}),
        ("IntegrationPackInstance", ("id", "integrationPackOverrideName", "integrationPackId"),
            {"put": False, "get": True, "query": True, "post": True, "delete": True}),
        ("IntegrationPackAtomAttachment", ("id", "atomId", "integrationPackInstanceId"),
            {"get": False, "put": False}),
        ("IntegrationPackEnvironmentAttachment",
            ("id", "environmentId", "integrationPackInstanceId"), {"put": False, "get": False}),
        ("Process", ("id", "name", "integrationpackInstanceId", "integrationpackId"),
            {"post": False, "put": False, "delete": False}),
        ("ProcessAtomAttachment", ("atomId", "processId", "id"), {"get": False, "put": False}),
        ("ProcessEnvironmentAttachment", ("environmentId", "processId", "id"),
            {"get": False, "put": False}),
        ("ProcessSchedules", ("id", "atomId", "Schedule", "processId"),
            {"post": False, "delete": False, "put": True}),
        ("ProcessScheduleStatus", ("enabled", "id", "atomId", "processId"),
            {"post": False, "delete": False}),
        ("Role", ("parentId", "name", "accountId", "id"),
            {"post": False, "get": False, "put": False, "delete": False}),
)

# Loop through all the entities we are creating via the factory and factory them!
for name, attrs, kwargs in entities:
    __all__.append(name)
    globals()[name] = Resource.create_resource(name, attrs, **kwargs)
