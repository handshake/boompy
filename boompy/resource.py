import copy
import json
import re

from datetime import datetime

from .errors import APIMethodNotAllowedError, BoomiError
from .base_api import API

DEFAULT_SUPPORTED = {
    "get": True,
    "query": True,
    "put": True,
    "post": True,
    "delete": True,
}

QUERY_OPERATOR_REGEX = re.compile("^(\w+?)(?:__(eq|not|like|gte?|lte?|starts?_with|null|not_null|between))?$")
QUERY_OPERATOR_LOOKUP = {
    "eq": "EQUALS",
    "not": "NOT_EQUALS",
    "like": "LIKE",
    "gt": "GREATER_THAN",
    "gte": "GREATER_THAN_OR_EQUAL",
    "lt": "LESS_THAN",
    "lte": "LESS_THAN_OR_EQUAL",
    "start_with": "STARTS_WITH",
    "starts_with": "STARTS_WITH",
    "null": "IS_NULL",
    "not_null": "IS_NOT_NULL",
    "between": "BETWEEN"
}

# A meta class that fakes the name of the class generated via the factory
class ResourceMeta(type):
    def __new__(cls, name, parents, dict_):
        name = dict_.get('_name', name)
        return super(ResourceMeta, cls).__new__(cls, name, parents, dict_)

class Resource(object):
    """ A base boomi resource. """

    _id_attr = None
    _attributes = tuple()
    _name = "Resource"
    _uri = None

    supported = DEFAULT_SUPPORTED

    @property
    @classmethod
    def __name__(cls):
        return cls.name

    def __init__(self, **kwargs):
        for attr in self._attributes:
            setattr(self, attr, None)

        # Go through the kwargs and if they are an attribute we expect, assigns the value to self.
        for key, value in kwargs.iteritems():
            if key in self._attributes:
                setattr(self, key, value)


    @classmethod
    def create_resource(cls, type_, attributes, id_attr="id", **supported_methods):
        """ Factory function which will return a class of type 'type_' """

        _supported = copy.copy(DEFAULT_SUPPORTED)
        _supported.update(supported_methods)

        class SubResource(Resource):
            __metaclass__ = ResourceMeta
            _uri = type_
            _name = type_
            _id_attr = id_attr
            _attributes = attributes
            supported = _supported

        return SubResource


    @classmethod
    def __https_request(cls, url, method="get", data=None):
        """ Validate that we can call this method, and then calls it on the API singleton """
        actual_method = method

        # Make sure we're checking capabilities againts real permissions, despite Boomi's silly rest
        # api using POST for everything.
        if "update" in url:
            actual_method = "put"
        elif "query" in url:
            actual_method = "query"

        if not cls.supported.get(actual_method):
            raise APIMethodNotAllowedError(method)

        if data is None:
            data = {}

        return API().https_request(url, method, data)


    def __update_attrs_from_response(self, res):
        """ Updates the attributes on self from the response object.
            We expect that all errors which will get raised will have already been raised. """
        res_json = json.loads(res.content)
        for attr in self._attributes:
            value = res_json.get(attr)
            if ("Date" in attr or "Time" in attr) and value:
                value = time.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            setattr(self, attr, value)


    def _serialize_value(self, value):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M:%SZ")
        return value


    def serialize(self):
        """ Serialize self for the payload getting sent to boomi. """
        return {k: self._serialize_value(getattr(self, k)) for k in self._attributes
                if getattr(self, k) is not None}


    @classmethod
    def get(cls, boomi_id):
        """ Returns a single instance of type cls if the ID passed in here is a valid entity. """

        resource = cls()
        res = cls.__https_request(resource.url(boomi_id=boomi_id), method="get")
        resource.__update_attrs_from_response(res)

        return resource


    @classmethod
    def query(cls, join="and", **kwargs):
        """ Returns a list of entities of type 'cls' matching the query kwargs passed. If left
            empty, is the equivilent of all() """
        expressions = []

        for key, value in kwargs.iteritems():
            if value is not None:
                operator = "EQUALS"
                prop, op = QUERY_OPERATOR_REGEX.match(key).groups()
                if op:
                    operator = QUERY_OPERATOR_LOOKUP[op]

                if not isinstance(value, list):
                    value = [value]

                expressions.append({
                    "argument": value,
                    "operator": operator,
                    "property": prop
                })

        if len(expressions) == 1:
            expressions = expressions[0]
        elif len(expressions) > 1:
            expressions = {
                "operator": join,
                "nestedExpression": expressions
            }

        if expressions:
            q = {"QueryFilter": {"expression": expressions}}
        else:
            q = {}

        # Do the initial query to get the first set of results
        res = cls.__https_request("%s/query" % cls.__base_url(), method="post", data=q)
        query_result = json.loads(res.content)
        result_objs = query_result.get("result", [])
        result_count = query_result.get("numberOfResults", len(result_objs))
        query_token = query_result.get("queryToken")
        response = cls.__process_query_result(result_objs)

        # If we need to do paging, lets continue to fetch the queryMore endpoint to fill up the
        # results set with all of the results.
        while len(response) < result_count:
            res = cls.__https_request("%s/queryMore" % cls.__base_url(), method="post",
                                      data=query_token)
            query_result = json.loads(res.content)
            result_objs = query_result.get("result", [])
            query_token = query_result.get("queryToken")
            response += cls.__process_query_result(result_objs)

        return response

    @classmethod
    def __process_query_result(cls, result_objs):
        response = []
        for payload in result_objs:
            entity = cls()
            response.append(entity)
            for attr in cls._attributes:
                value = payload.get(attr)
                if ("Date" in attr or "Time" in attr) and value:
                    value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
                setattr(entity, attr, value)

        return response

    def save(self, **kwargs):
        """ Updates or creates self on boomi. """
        url = self.url()

        if getattr(self, self._id_attr) is not None:
            url = "%s/update" % url

        res = self.__https_request(self.url(), method="post", data=self.serialize())
        self.__update_attrs_from_response(res)


    def delete(self, **kwargs):
        if getattr(self, self._id_attr) is None:
            raise BoomiError("Cannot call delete() on object which has not been saved yet.")

        self.__https_request(self.url(), method="delete", data=self.serialze())


    @classmethod
    def __base_url(cls):
        """ Returns the base url for this entity joined with the base on the api singleton. """
        base_url = API().base_url()
        return "%s/%s" % (base_url, cls._uri)


    def url(self, boomi_id=None):
        """ Returns the corresponding url for this instance depending on whether we are being
            created or are simply updating/getting."""
        if getattr(self, self._id_attr) is None and boomi_id is None:
            return self.__base_url()

        base_url = API().base_url()
        boomi_id = getattr(self, self._id_attr) if boomi_id is None else boomi_id
        return "%s/%s/%s" % (base_url, self._uri, boomi_id)

