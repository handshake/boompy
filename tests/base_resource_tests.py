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
    boomi = API(1,2,3)

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



