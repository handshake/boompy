import functools
import json
import time

import boompy
from .base_api import API
from .errors import UnauthorizedError, BoomiError

api = API()

def getAssignableRoles():
    """ Returns a list of assignable Role objects. """
    results = []
    res = api.https_request("%s/getAssignableRoles" % api.base_url(), "get", {})

    for role in json.loads(res.content).get("Role"):
        results.append(boompy.Role(**role))

    return results

def executeProcess(process_id, atom_id):
    data = {"processId": process_id, "atomId": atom_id}
    api.https_request("%s/executeProcess" % api.base_url(), "post", data)

def provisionPartnerCustomerAccount(data=None):
    """
    Method that will use the Boomi action to provision a new account for
    the data passed in, if the required field(s) are missing from the dictionary
    then a Boomi Error is raised
    """

    if data is None:
        data = {}

    PROVISION_FIELDS = {"name", "street", "city", "stateCode", "zipCode",
                        "countryCode", "status", "product"}

    # It takes about a minute for this process to complete
    base_url = "%s/AccountProvision" % api.base_url(partner=True)

    missing_fields = PROVISION_FIELDS - set(data.keys())

    if not missing_fields:
        res = api.https_request("%s/execute" % base_url, "post", data)
        results = json.loads(res.content)

        # According to Boomi docs looks like status will only be pending or completed
        while results.get("status") == "PENDING":
            time.sleep(2)
            result = api.https_request("%s/%s" % (base_url, results.get("id")), "get", {})
            results = json.loads(result.content)
        if results.get("status") != "COMPLETED":
            raise BoomiError("failed provisioning account, status=%s" % results.get("status"))
        else:
            return results
    else:
        raise BoomiError(("incomplete provison data provided, you are missing "
                          "the following fields: ") + str(list(missing_fields)))

def updatePartnerCustomerAccount(account_id, data=None):
    """
    Method that will use the Boomi action to update an account for the data
    passed in
    """

    if data is None:
        data = {}

    if data.get("id") is None:
        raise BoomiError("missing the field id in dict")
    elif data.get("id") != account_id:
        raise BoomiError("account_id passed in and id in dict do not match")

    base_url = "%s/AccountProvision/%s" % (api.base_url(partner=True), account_id)

    res = api.https_request(base_url, "post", data)
    results = json.loads(res.content)

    if results.get("status") != "COMPLETED":
        raise BoomiError("failed updating account, status=%s" % results.get("status"))
    else:
        return results
