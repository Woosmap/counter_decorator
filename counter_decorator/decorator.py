import os
from functools import wraps
import time

from .cua import EnvironmentConfig, Queue

PRIVATE_KEY = "private_key"
PUBLIC_KEY = "public_key"

config = EnvironmentConfig(keys_prefix='COUNTER_')

queue = Queue(config)


def _project_key_lambda(*args, **kwargs):
    return kwargs.get("project_key"), PUBLIC_KEY


def _get_organization_from_token(readable_token):
    instance = readable_token['instance']

    try:
        if instance['is_staff'] or instance['is_superuser']:
            return None
    except KeyError:
        pass

    return instance['organization']


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
