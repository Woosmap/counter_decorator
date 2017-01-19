import os
from functools import wraps
import time
import logging
from .cua import EnvironmentConfig, Queue

logger = logging.getLogger('counter_decorator')

PRIVATE_KEY = "private_key"
PUBLIC_KEY = "public_key"

try:
    config = EnvironmentConfig(keys_prefix='COUNTER_')
    queue = Queue(config)
except KeyError:
    raise Exception("Missing cua environment config")


def _project_key_lambda(*args, **kwargs):
    return kwargs.get("project_key"), PUBLIC_KEY


def _get_organization_from_token(readable_token):
    instance = readable_token['instance']

    is_admin = False

    try:
        is_admin = instance['is_staff'] or instance['is_superuser']
    except KeyError:
        # instance has no is_staff or is_superuser keys if the token is got with a public or private key.
        is_admin = False
    finally:
        return None if is_admin else instance["organization"]


def count_request(request_name, project_key_lambda=None, headers_lambda=None, name_lambda=None):
    if not project_key_lambda:
        project_key_lambda = _project_key_lambda

    def build_job_data(product, kind, organization):
        data = None
        if product is not None:
            data = {
                'product': product,
                'kind': kind,
                'ts': time.time(),
                'organization': organization
            }
        return data

    def wrapped(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            product = os.environ.get("PRODUCT_NAME")
            readable_token = kwargs['readable_token']
            key, kind_key = project_key_lambda(*args, **kwargs)
            kind = name_lambda(product, key, kind_key, *args, **kwargs) if name_lambda else request_name

            organization = _get_organization_from_token(readable_token)

            if organization:
                data = build_job_data(product, kind, organization)
                queue.put(data)

            return f(*args, **kwargs)

        return wrapper

    return wrapped
