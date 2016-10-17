import requests
import os
from functools import wraps


def project_key_lambda(*args, **kwargs):
    return kwargs.get("project_key")

def count_request(request_name, project_key_lambda=project_key_lambda):
    def wrapped(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            product = os.environ.get("PRODUCT_NAME")
            host = os.environ.get("COUNTER_HOST")
            key = project_key_lambda(*args, **kwargs)
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
