import copy
import json
import re
import time

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

class ResourceList(list):
    """ Used to handle lazy loading and paging through results from boomi.
        Idea cribbed from https://github.com/recurly/recurly-client-python/
    """

    def __iter__(self):
        list_ = self
        while list_:
            for x in list.__iter__(list_):
                yield x
            list_ = list_.__next_page()

    def __len__(self):
        return self.result_count

    def __actual_len(self):
        return super(ResourceList, self).__len__()

    def __next_page(self):
        time.sleep(.2)
        if not self.query_token or self.__actual_len() < 100:
            raise StopIteration

        res = self.resource._https_request("%s/queryMore" % self.resource._base_url(),
                                           method="post", data=self.query_token)

        return ResourceList.page_for_response(self.resource, res)

    @classmethod
    def __process_obj_results(cls, resource, result_objs):
        response = []
        for payload in result_objs:
            entity = resource()
            response.append(entity)
            entity._update_attrs_from_response(payload)

        return response

    @classmethod
    def page_for_response(cls, resource, response):
        query_result = json.loads(response.content)
        result_objs = cls.__process_obj_results(resource, query_result.get("result", []))
        list_ = cls(result_objs)
        list_.resource = resource
        list_.result_count = query_result.get("numberOfResults", len(result_objs))
        list_.query_token = query_result.get("queryToken")

        return list_


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
    def _https_request(cls, url, method="get", data=None):
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


    def _update_attrs_from_response(self, payload):
        """ Updates the attributes on self from the response object.
            We expect that all errors which will get raised will have already been raised. """
        for attr in self._attributes:
            value = payload.get(attr)
            processing = [value]
            while processing:
                current = processing.pop()
                if isinstance(current, list):
                    processing.extend(current)
                elif isinstance(current, dict):
                    if current.get("@type"):
                        del current["@type"]
                    processing.extend(current.values())
            if ("Date" in attr or "Time" in attr) and value:
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
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
        res = cls._https_request(resource.url(boomi_id=boomi_id), method="get")
        resource._update_attrs_from_response(json.loads(res.content))

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
        res = cls._https_request("%s/query" % cls._base_url(), method="post", data=q)
        return ResourceList.page_for_response(cls, res)

    def save(self, **kwargs):
        """ Updates or creates self on boomi. """
        url = self.url()

        if getattr(self, self._id_attr) is not None:
            url = "%s/update" % url

        res = self._https_request(url, method="post", data=self.serialize())
        self._update_attrs_from_response(json.loads(res.content))


    def delete(self, **kwargs):
        if getattr(self, self._id_attr) is None:
            raise BoomiError("Cannot call delete() on object which has not been saved yet.")

        self._https_request(self.url(), method="delete", data=self.serialize())


    @classmethod
    def _base_url(cls):
        """ Returns the base url for this entity joined with the base on the api singleton. """
        base_url = API().base_url()
        return "%s/%s" % (base_url, cls._uri)


    def url(self, boomi_id=None):
        """ Returns the corresponding url for this instance depending on whether we are being
            created or are simply updating/getting."""
        if getattr(self, self._id_attr) is None and boomi_id is None:
            return self._base_url()

        base_url = API().base_url()
        boomi_id = getattr(self, self._id_attr) if boomi_id is None else boomi_id
        return "%s/%s/%s" % (base_url, self._uri, boomi_id)
