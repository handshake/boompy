import json

class BoomiError(Exception):
    pass


class UnauthorizedError(BoomiError):
    pass


class InterfaceError(BoomiError):
    def __init__(self, arg):
        super(InterfaceError, self).__init__()
        self.message = "%s is not allowed for this method on this object type" % arg


class APIRequestError(BoomiError):

    def __init__(self, res):
        super(APIRequestError, self).__init__()
        try:
            message = json.loads(res.content).get("message")
        except ValueError:
            message = res.content

        self.message = "%s: %s" % (res.status_code, message)

    def __str__(self):
        return self.message


class NotFoundError(APIRequestError):
    pass

class RateLimitError(APIRequestError):
    pass

class APIMethodNotAllowedError(BoomiError):
    def __init__(self, method):
        super(APIMethodNotAllowedError, self).__init__()
        self.method = method

    @property
    def message(self):
        return "Sorry, %s is not allowed on this type" % self.method

    def __str__(self):
        return self.message
