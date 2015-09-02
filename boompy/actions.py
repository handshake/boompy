import functools
import json

import boompy
from .base_api import API
from .errors import UnauthorizedError

def getAssignableRoles():
    """ Returns a list of assignable Role objects. """
    results = []
    res = API().https_request("%s/getAssignableRoles" % API().base_url(), "get", {})

    for role in json.loads(res.content).get("Role"):
        results.append(boompy.Role(**role))

    return results

def executeProcess(process_id, atom_id):
    data = {"processId": process_id, "atomId": atom_id}
    API().https_request("%s/executeProcess" % API().base_url(), "post", data)
