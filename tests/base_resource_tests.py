import mock
from nose.tools import raises

import boompy

from boompy.base_api import API
from boompy.resource import Resource
from boompy.errors import APIMethodNotAllowedError

def test_create_resource():
    TestType = Resource.create_resource("TestType", ("thing1", "thing2"), id_attr="thing1",
                                        query=False, put=False)
    newthing = TestType(thing1=1, thing2="testing", thing3="not a thing")
    assert newthing.thing1 == 1
    assert newthing.thing2 == "testing"
    assert type(newthing) == TestType
    assert not hasattr(newthing, "thing3")

def test_inherit_resource():
    class TestType(Resource):
        _id_attr = "id"
        _attributes = ("attr1",)
        _name = "TestType"
        _uri = None
        supported = {"put": False, "get": True, "delete": True}

    newthing = TestType(attr1="hello")
    assert newthing.attr1 == "hello"

@raises(APIMethodNotAllowedError)
@mock.patch.object(API, "https_request")
def test_https_request(request_mock):
    boomi = API()._set_auth("account_id", "username", "password")

    class MockResponse(object):
        def __init__(self, content=None):
            self.content = content

    request_mock.return_value = MockResponse(content='{"id": 123}')

    class TestType(Resource):
        _id_attr = "id"
        _attributes = ("id",)
        _name = "TestType"
        _uri = None
        _api = boomi
        supported = {"get": True, "query": False}

    newthing = TestType(id="hello")

    newthing.get("123")
    assert request_mock.called

    newthing.query()

def test__update_attrs_from_response():
    TestType = Resource.create_resource("TestType", ("thing1", "thing2"), id_attr="thing1")
    newthing = TestType(thing1=1, thing2="testing")
    new_1 = 2
    new_2 = {"@type": "TestList",
             "list": [{"@type": "TestObj", "id": 0}, {"@type": "TestObj", "id": 1}],
             "id": 1}
    newthing._update_attrs_from_response({"thing1": new_1, "thing2": new_2})
    assert newthing.thing1 == new_1
    assert newthing.thing2.get("@type") is None
    assert newthing.thing2.get("id") == 1
    assert len(newthing.thing2.get("list")) == 2
    for num in (0, 1):
        assert newthing.thing2.get("list")[num].get("@type") is None
        assert newthing.thing2.get("list")[num].get("id") == num

def test_atom_resource_has_attribute():
    """
    Method to test if newly added attributes exist in the API resource
    """
    atom_attributes = boompy.Atom._attributes
    added_attributes = ("cloudId",)

    for key in added_attributes:
        assert key in atom_attributes, "%s is not an Atom attribute." % key
