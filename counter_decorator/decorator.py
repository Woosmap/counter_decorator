import requests
import os
from functools import wraps

PRIVATE_KEY = "private_key"
PUBLIC_KEY = "public_key"


def _project_key_lambda(*args, **kwargs):
    return kwargs.get("project_key"), PUBLIC_KEY


def count_request(request_name, project_key_lambda=None, headers_lambda=None, name_lambda=None):
    if not project_key_lambda:
        project_key_lambda = _project_key_lambda

    def build_counter_resource(host, key, product, kind, kind_key=PUBLIC_KEY):
        counter_resource = None
        if host is not None and product is not None and key is not None:
            query_name = "key" if kind_key == PUBLIC_KEY else "private_key"
            counter_resource = "http://{host}/products/{product}/kinds/{kind}?{query_name}={key}".format(
                host=host,
                query_name=query_name,
                key=key,
                product=product,
                kind=kind)
        return counter_resource

    def wrapped(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            product = os.environ.get("PRODUCT_NAME")
            host = os.environ.get("COUNTER_HOST")
            key, kind_key = project_key_lambda(*args, **kwargs)
            kind = name_lambda(product, key, kind_key, *args, **kwargs) if name_lambda else request_name
            counter_resource = build_counter_resource(host, key, product, kind, kind_key)
            if counter_resource:
                headers = headers_lambda(*args, **kwargs) if headers_lambda else {}
                try:
                    r = requests.post(counter_resource, headers=headers)
                except requests.exceptions.ConnectionError:
                    # we should log something here about the error
                    pass
                else:
                    kwargs["counter_response_status_code"] = r.status_code

            return f(*args, **kwargs)

        return wrapper

    return wrapped
