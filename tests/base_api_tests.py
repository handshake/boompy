import mock
import requests

from nose.tools import raises

from boompy.base_api import API, BASE_URL, PARTNER_BASE_URL
from boompy.errors import UnauthorizedError

def test_set_auth():
    api = API()
    assert api.account_id is None
    assert api.username is None
    assert api.password is None

    api._set_auth("account_id", "username", "password")

    assert api.account_id == "account_id"
    assert api.username == "username"
    assert api.password == "password"

@raises(UnauthorizedError)
def test_base_url_error():
    api = API()
    api.base_url()

def test_base_url_no_partner():
    api = API()
    api.account_id = "test"
    expected = "%s/test" % BASE_URL
    assert api.base_url() == expected

def test_base_url_partner():
    api = API()
    api.account_id = "test"
    expected = "%s/test" % PARTNER_BASE_URL
    assert api.base_url(partner=True) == expected

@raises(UnauthorizedError)
def test_session_with_headers_no_username():
    api = API()
    api._set_auth("account_id", None, "password")
    api.session_with_headers()

@raises(UnauthorizedError)
def test_session_with_headers_no_password():
    api = API()
    api._set_auth("account_id", "username", None)
    api.session_with_headers()

def test_session_with_headers():
    api = API()
    api._set_auth("account_id", "username", "password")
    session = api.session_with_headers()
    assert session.auth == ("username", "password")
    assert session.headers.get("Content-Type") == "application/json"
    assert session.headers.get("Accept") == "application/json"


@mock.patch.object(requests.Session, "get")
def test_https_request_basic(get_patch):

    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 200
    get_patch.return_value = res_patch
    api = API()
    api._set_auth("account_id", "username", "password")
    res = api.https_request("a real url", "get", {"test": 1})

