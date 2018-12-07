PUBLIC_KEY = "public_key"
PRIVATE_KEY = "private_key"

QUOTA_MULTIPLIERS = {
    "RECO_CONTRIBUTION": 0,
    "RECO": 1,
    "STORES_DATABASE": 1,
    "ZONES_DATABASE": 1,
    "RECO_USAGE": 0,
    "RECO_INTERNAL_USAGE": 0,
    "STORES_SEARCHES": 1,
    "STORES_INTERNAL_USAGE": 0,
    "STORES": 10
}


def project_key_lambda(*args, **kwargs):
    return kwargs.get("project_key"), PUBLIC_KEY


def organization_from_token(readable_token, **kwargs):
    project_id = kwargs.get('project_id')
    organization_id = kwargs.get('organization_id')

    instance = readable_token['instance']
    is_admin = False

    try:
        is_admin = instance['is_staff'] or instance['is_superuser']
    except KeyError:
        # instance has no is_staff or is_superuser keys if the token is got with a public or private key.
        is_admin = False
    finally:
        if is_admin:
            if project_id is not None and organization_id is not None:
                return {
                    'pk': organization_id,
                    'project_pk': project_id
                }
            return None
        else:
            return instance["organization"]
