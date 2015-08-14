import functools
import json

import boompy
from .errors import UnauthorizedError

def getAssignableRoles():
    if boompy.api is None:
        raise UnauthorizedError("No authentication is set up. Please call `set_auth`")

    results = []
    res = boompy.api.https_request("%s/getAssignableRoles" % boompy.api.base_url(), "get", {})

    for role in json.loads(res.content).get("Role"):
        results.append(boompy.Role(**role))

    return results
