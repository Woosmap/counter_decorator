import requests
import os
from functools import wraps


def count_request(request_name, project_key_parent=None, project_key_name="project_key"):
    def wrapped(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            product = os.environ.get("PRODUCT_NAME")
            host = os.environ.get("COUNTER_HOST")
            if project_key_parent is None:
                key = kwargs.get(project_key_name)
            else:
                _parents = project_key_parent.split(".")
                try:
                    parent = kwargs[_parents.pop(0)]
                except KeyError:
                    key = None
                else:
                    for _p in _parents:
                        try:
                            parent = getattr(parent, _p)
                        except AttributeError:
                            break
                    try:
                        key = parent.get(project_key_name)
                    except AttributeError:
                        key = None

            if host is not None and product is not None and key is not None:
                counter_resource = "http://{host}/projects/{key}/products/{product}/kinds/{kind}".format(
                    host=host,
                    key=key,
                    product=product,
                    kind=request_name)
                try:
                    r = requests.post(counter_resource)
                except requests.exceptions.ConnectionError:
                    # we should log something here about the error
                    pass

            return f(*args, **kwargs)

        return wrapper

    return wrapped
