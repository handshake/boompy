import functools
import json

from .base_api import API
from .errors import UnauthorizedError

def getAssignableRoles():
    results = []
    res = API().https_request("%s/getAssignableRoles" % boompy.api.base_url(), "get", {})

    for role in json.loads(res.content).get("Role"):
        results.append(boompy.Role(**role))

    return results
