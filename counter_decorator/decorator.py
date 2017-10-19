import logging
import os
from functools import wraps
from . import queue
from .cua import build_job_data
from .utils import (organization_from_token, project_key_lambda as default_project_key_lambda, QUOTA_MULTIPLIERS)

logger = logging.getLogger(__name__)


def count_request(request_name, product=None, project_key_lambda=None, headers_lambda=None, name_lambda=None):
    project_key_lambda = project_key_lambda if project_key_lambda else default_project_key_lambda
    product = product if product else os.environ.get("PRODUCT_NAME")

    def wrapped(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key, kind_key = project_key_lambda(*args, **kwargs)
            kind = name_lambda(product, key, kind_key, *args, **kwargs) if name_lambda else request_name
            organization = organization_from_token(kwargs['readable_token'])
            if product not in QUOTA_MULTIPLIERS:
                logger.error("%s is not a valid product" % product)

            data = build_job_data(product, kind, organization)
            queue.put(data)
            return f(*args, **kwargs)

        return wrapper

    return wrapped
