import mock
import requests

from nose.tools import raises

from boompy.boompy import Boompy, BASE_URL, PARTNER_BASE_URL
from boompy.errors import UnauthorizedError, NotFoundError, RateLimitError

def test_init():
    api = Boompy("account_id", "username", "password")
    assert api.account_id == "account_id"
    assert api.username == "username"
    assert api.password == "password"

def test_base_url_no_partner():
    api = Boompy("account_id", "username", "password")
    api.account_id = "test"
    expected = "%s/test" % BASE_URL
    assert api.base_url() == expected

def test_base_url_partner():
    api = Boompy("account_id", "username", "password")
    api.account_id = "test"
    expected = "%s/test" % PARTNER_BASE_URL
    assert api.base_url(partner=True) == expected

@raises(UnauthorizedError)
def test_init_with_no_username():
    api = Boompy("account_id", None, "password")

@raises(UnauthorizedError)
def test_init_with_no_password():
    api = Boompy("account_id", "username", None)

def test_session_with_headers():
    api = Boompy("account_id", "username", "password")
    session = api.session_with_headers()
    assert session.auth == ("username", "password")
    assert session.headers.get("Content-Type") == "application/json"
    assert session.headers.get("Accept") == "application/json"

@mock.patch.object(requests.Session, "get")
def test_https_request_basic(get_patch):
    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 200
    get_patch.return_value = res_patch
    api = Boompy("account_id", "username", "password")
    res = api.https_request("a real url", "get", {"test": 1})

@mock.patch.object(requests.Session, "get")
@raises(NotFoundError)
def test_https_request_not_found(get_patch):
    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 404
    res_patch.content = "{'message': 'testing'}"
    get_patch.return_value = res_patch
    api = Boompy("account_id", "username", "password")
    res = api.https_request("a real url", "get", {"test": 1})

@mock.patch.object(requests.Session, "get")
@raises(RateLimitError)
def test_https_request_service_unavailable(get_patch):
    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 503
    res_patch.content = "{'message': 'testing'}"
    get_patch.return_value = res_patch
    api = Boompy("account_id", "username", "password")
    res = api.https_request("a real url", "get", {"test": 1})

@mock.patch.object(requests.Session, "get")
@raises(RateLimitError)
def test_https_request_too_many(get_patch):
    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 429
    res_patch.content = "{'message': 'testing'}"
    get_patch.return_value = res_patch
    api = Boompy("account_id", "username", "password")
    res = api.https_request("a real url", "get", {"test": 1})
