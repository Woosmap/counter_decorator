from .cua import EnvironmentConfig, Queue, build_job_data

try:
    config = EnvironmentConfig(keys_prefix='COUNTER_')
except KeyError:
    raise Exception("Missing cua environment config")
else:
    queue = Queue(config)
