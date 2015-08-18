import json

class BoomiError(Exception):
    """ A general boomi exception """
    pass


class UnauthorizedError(BoomiError):
    """ Raised when you are not fully authed for the boomi api """
    pass


class InterfaceError(BoomiError):
    """ An exception raised when you call something in this library wrong. """
    def __init__(self, arg):
        super(InterfaceError, self).__init__()
        self.message = "%s is not allowed for this method on this object type" % arg


class APIRequestError(BoomiError):
    """ A general api request error. """

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
    """ An http request error. Raised when 404 """
    pass

class RateLimitError(APIRequestError):
    """ Raised when boomi tells you you've been bad. """
    pass

class APIMethodNotAllowedError(BoomiError):
    """ Raised when you try to call an http method on an entity which doesnt support it. """
    def __init__(self, method):
        super(APIMethodNotAllowedError, self).__init__()
        self.method = method

    @property
    def message(self):
        return "Sorry, %s is not allowed on this type" % self.method

    def __str__(self):
        return self.message
