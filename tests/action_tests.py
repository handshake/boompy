import boompy
import json
import mock
import requests

from nose.tools import raises

def make_mock_json_response(json_data):
    """
    Helper function that returns a mock http response for the provided json
    """

    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 200
    res_patch.content = json.dumps(json_data)
    return res_patch

@raises(boompy.errors.BoomiError)
def test_provision_with_no_data():
    """
    Test to see if a BoomiError is thrown when trying to provision an account_id
    with no data
    """

    boompy.set_auth("account_id", "username", "password")
    boompy.actions.provisionPartnerCustomerAccount({})

@raises(boompy.errors.BoomiError)
def test_provision_with_missing_data():
    """
    Test to see if a BoomiError is thrown when trying to provision an account_id
    with missing data / fields
    """

    fake_data = {
        "name": "HelloWorld",
        "street": "Fake Street"
    }

    boompy.set_auth("account_id", "username", "password")
    boompy.actions.provisionPartnerCustomerAccount(fake_data)

@mock.patch.object(requests.Session, "get", autospec=True)
@mock.patch.object(requests.Session, "post", autospec=True)
def test_successful_provision_account(post_patch, get_patch):
    """
    Test to simulate a successful account provision
    """

    fake_data = {
        "name": "HelloWorld",
        "street": "Fake Street",
        "city": "Fake City",
        "stateCode": "NA",
        "zipCode": "00000",
        "countryCode": "NA",
        "status": "trial",
        "product": [{"productCode": "fake", "quantity": 1}]
    }

    fake_post_content = {
        "@type": "AccountProvisionResult",
        "id": "0123456789ABCDEFGH",
        "status": "PENDING"
    }

    fake_get_content = {
        "@type": "AccountProvisionResult",
        "status": "COMPLETED",
        "accountId": "podnersub-0A1B2C",
        "id": "0123456789ABCDEFGH"
    }

    post_patch.return_value = make_mock_json_response(fake_post_content)
    get_patch.return_value = make_mock_json_response(fake_get_content)
    boompy.set_auth("account_id", "username", "password")
    result = boompy.actions.provisionPartnerCustomerAccount(fake_data)
    assert result.get("accountId") == fake_get_content.get("accountId")
    assert result.get("status") == fake_get_content.get("status")

@mock.patch.object(requests.Session, "post", autospec=True)
@raises(boompy.errors.BoomiError)
def test_failed_provision_account(post_patch):
    """
    Test to simulate a failed account provision
    """

    fake_data = {
        "name": "HelloWorld",
        "street": "Fake Street",
        "city": "Fake City",
        "stateCode": "NA",
        "zipCode": "00000",
        "countryCode": "NA",
        "status": "trial",
        "product": [{"productCode": "fake", "quantity": 1}]
    }

    # According to Boomi docs looks like status will only be pending or completed
    fake_content = {
        "@type": "AccountProvisionResult",
        "status": "NOT PENDING OR COMPLETED"
    }

    post_patch.return_value = make_mock_json_response(fake_content)
    boompy.set_auth("account_id", "username", "password")
    boompy.actions.provisionPartnerCustomerAccount(fake_data)

@raises(boompy.errors.BoomiError)
def test_update_with_no_data():
    """
    Test to see if a BoomiError is thrown when trying to update an account
    with no data
    """

    fake_account_id = "FakeAccount-12345"
    boompy.set_auth("account_id", "username", "password")
    boompy.actions.updatePartnerCustomerAccount(fake_account_id, {})

@raises(boompy.errors.BoomiError)
def test_update_with_missing_id():
    """
    Test to see if a BoomiError is thrown when trying to update an account
    with missing id field
    """

    fake_account_id = "FakeAccount-12345"
    fake_data = {
        "street": "Fake Street"
    }

    boompy.set_auth("account_id", "username", "password")
    boompy.actions.updatePartnerCustomerAccount(fake_account_id, fake_data)

@raises(boompy.errors.BoomiError)
def test_update_with_mismatch():
    """
    Test to see if a BoomiError is thrown when trying to update an account
    when account_id and id field do not match
    """

    fake_account_id = "FakeAccount-12345"
    fake_data = {
        "id": "FakeAccount2-43215",
        "street": "Fake Street"
    }

    boompy.set_auth("account_id", "username", "password")
    boompy.actions.updatePartnerCustomerAccount(fake_account_id, fake_data)

@mock.patch.object(requests.Session, "post", autospec=True)
def test_successful_update_on_account(post_patch):
    """
    Test to simulate a successful account update
    """

    fake_account_id = "FakeAccount-12345"
    fake_data = {
        "id": fake_account_id,
        "name": "HelloWorld",
        "street": "Fake Street",
        "city": "Fake City",
        "stateCode": "NA",
        "zipCode": "00000",
        "countryCode": "NA",
        "status": "trial",
        "product": [{"productCode": "fake", "quantity": 1}]
    }

    fake_content = {
        "@type": "AccountProvisionResult",
        "status": "COMPLETED"
    }

    post_patch.return_value = make_mock_json_response(fake_content)
    boompy.set_auth("account_id", "username", "password")
    boompy.actions.updatePartnerCustomerAccount(fake_account_id, fake_data)

@mock.patch.object(requests.Session, "post", autospec=True)
@raises(boompy.errors.BoomiError)
def test_failed_update_on_account(post_patch):
    """
    Test to simulate a failed account update
    """

    fake_account_id = "FakeAccount-12345"
    fake_data = {
        "id": fake_account_id,
        "name": "HelloWorld",
        "street": "Fake Street",
        "city": "Fake City",
        "stateCode": "NA",
        "zipCode": "00000",
        "countryCode": "NA",
        "product": [{"productCode": "fake", "quantity": 1}]
    }

    fake_content = {
        "@type": "AccountProvisionResult",
        "status": "NOT PENDING OR COMPLETED"
    }

    post_patch.return_value = make_mock_json_response(fake_content)
    boompy.set_auth("account_id", "username", "password")
    boompy.actions.updatePartnerCustomerAccount(fake_data)
