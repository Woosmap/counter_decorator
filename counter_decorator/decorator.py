import os
from functools import wraps
import time

import logging

from . import requests_session
from .cua import EnvironmentConfig, Queue

logger = logging.getLogger('counter_decorator')

PRIVATE_KEY = "private_key"
PUBLIC_KEY = "public_key"

HAS_ASYNC_COUNTER = False

try:
    config = EnvironmentConfig(keys_prefix='COUNTER_')
    queue = Queue(config)
    HAS_ASYNC_COUNTER = True
    logger.info('Using cua to increment counters.')
except KeyError:
    logger.info('Using http to increment counter.')


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
    count_func = count_request_redis if HAS_ASYNC_COUNTER else count_request_http

    return count_func(request_name, project_key_lambda, headers_lambda, name_lambda)


def count_request_http(request_name, project_key_lambda=None, headers_lambda=None, name_lambda=None):
    if not project_key_lambda:
        project_key_lambda = _project_key_lambda

    def build_counter_resource(host, key, product, kind, kind_key=PUBLIC_KEY):
        counter_resource = None
        query_name = "key" if kind_key == PUBLIC_KEY else "private_key"
        if host is not None and product is not None and key is not None:
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
                    r = requests_session.post(counter_resource, headers=headers)
                except requests.exceptions.ConnectionError:
                    logger.exception('An exception has occurred while connecting to the counter host.')
                    pass
                else:
                    kwargs["counter_response_status_code"] = r.status_code

            return f(*args, **kwargs)

        return wrapper

    return wrapped


def count_request_redis(request_name, project_key_lambda=None, headers_lambda=None, name_lambda=None):
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
