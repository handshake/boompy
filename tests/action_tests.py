import mock
import requests
import json

from nose.tools import raises

import boompy

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

@mock.patch.object(requests.Session, "post")
def test_successful_provision_account(get_patch):
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

    fake_content = {
        "@type": "AccountProvisionResult",
        "status": "COMPLETED",
        "accountId": "podnersub-0A1B2C",
        "id": "0123456789ABCDEFGH"
    }

    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 200
    res_patch.content = json.dumps(fake_content)
    get_patch.return_value = res_patch
    boompy.set_auth("account_id", "username", "password")
    boompy.actions.provisionPartnerCustomerAccount(fake_data)

@mock.patch.object(requests.Session, "post")
@raises(boompy.errors.BoomiError)
def test_failed_provision_account(get_patch):
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

    res_patch = mock.Mock(spec=requests.Response)
    res_patch.status_code = 200
    res_patch.content = json.dumps(fake_content)
    get_patch.return_value = res_patch
    boompy.set_auth("account_id", "username", "password")
    boompy.actions.provisionPartnerCustomerAccount(fake_data)
