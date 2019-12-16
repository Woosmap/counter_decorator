import logging
import os
from functools import wraps
from . import queue
from woosutils.cua import build_job_data
from .utils import (organization_from_token, project_key_lambda as default_project_key_lambda, QUOTA_MULTIPLIERS)

logger = logging.getLogger(__name__)


def count_request(request_name, product=None, project_key_lambda=None, headers_lambda=None, name_lambda=None,
                  organization_from_token_lambda=None):
    """Counts the request, must be placed after an HasPermissionDecorator"""
    project_key_lambda = project_key_lambda if project_key_lambda else default_project_key_lambda
    product = product if product else os.environ.get("PRODUCT_NAME")

    def wrapped(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key, kind_key = project_key_lambda(*args, **kwargs)
            kind = name_lambda(product, key, kind_key, *args, **kwargs) if name_lambda else request_name
            if product not in QUOTA_MULTIPLIERS:
                logger.error("%s is not a valid product" % product)

            organization_extractor = organization_from_token_lambda or organization_from_token

            organization = organization_extractor(kwargs['readable_token'], **kwargs)

            if organization is not None:
                data = build_job_data(product, kind, organization)
                queue.put(data)
            else:
                logger.error('Cannot build a job data without organization.\n {request_name}, {product}, {kind}'.format(
                    request_name=request_name,
                    product=product,
                    kind=kind
                ))
            return f(*args, **kwargs)

        return wrapper

    return wrapped
