# coding=utf-8
import os
import traceback
from uuid import uuid4
import time
import redis
import logging
import json
from threading import Thread

logger = logging.getLogger('cua')


class Config(object):
    def __init__(self, prefix, host, port, database, enabled):
        self.HOST = host
        self.PORT = port
        self.DATABASE = database
        self.PREFIX = prefix
        self.ENABLED = enabled


class EnvironmentConfig(Config):
    def __init__(self, keys_prefix):
        host = os.environ[keys_prefix + 'REDIS_HOST']
        database = os.environ[keys_prefix + 'REDIS_DATABASE']
        prefix = os.environ[keys_prefix + 'REDIS_QUEUE_PREFIX']
        port = os.environ.get(keys_prefix + 'REDIS_PORT', 6379)
        enabled = os.environ.get(keys_prefix + 'ENABLED', 'yes') == 'yes'
        super(EnvironmentConfig, self).__init__(prefix, host, port, database, enabled)


class Queue(object):
    def __init__(self, config):
        config = config
        self._redis = redis.StrictRedis(host=config.HOST, port=config.PORT, db=config.DATABASE)

        self.prefix = config.PREFIX
        self.enabled = config.ENABLED
        self.todo_name = self.prefix + ':todo'
        self.doing_name = self.prefix + ':doing'
        self.failed_name = self.prefix + ':failed'

    def put(self, data):
        if not self.enabled:
            return None
        job_id = self.prefix + '-' + str(uuid4())
        job_data = {'t': time.time(), 'data': data}

        pipeline = self._redis.pipeline()
        pipeline.set(job_id, json.dumps(job_data))
        pipeline.lpush(self.todo_name, job_id)
        pipeline.execute()
        return job_id

    def get(self):
        job_id = self._redis.brpoplpush(self.todo_name, self.doing_name)
        raw_data = self._redis.get(job_id)
        data = json.loads(raw_data.decode('utf-8'))

        return job_id.decode('utf-8'), data

    def mark_done(self, job_id):
        pipeline = self._redis.pipeline()
        pipeline.lrem(self.doing_name, 1, job_id)
        pipeline.delete(job_id)
        pipeline.execute()

    def mark_failed(self, job_id, e, trace):
        job_data = json.loads(self._redis.get(job_id).decode('utf-8'))
        job_data['exception'] = {'message': str(e), 'trace': trace}

        pipeline = self._redis.pipeline()
        pipeline.lrem(self.doing_name, 1, job_id)
        pipeline.rpush(self.failed_name, job_id)
        pipeline.set(job_id, json.dumps(job_data))
        pipeline.execute()

    def get_todo_count(self):
        return self._redis.llen(self.todo_name)

    def get_doing_count(self):
        return self._redis.llen(self.doing_name)

    def get_failed_count(self):
        return self._redis.llen(self.failed_name)

    def _cleanup(self):
        self._redis.delete(self.todo_name, self.doing_name, self.failed_name)


class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """

    def __init__(self, queue, func=None):
        Thread.__init__(self)
        self.queue = queue
        self.daemon = True
        self.should_exit = False
        self.func = func
        self.start()

    def run(self):
        while not self.should_exit:
            job_id, data = self.queue.get()
            try:

                if self.func:
                    self.func(job_id, data)

            except Exception as e:
                logger.exception('An exception occurred while handling a Job')
                self.queue.mark_failed(job_id, e, traceback.format_exc())
            else:
                self.queue.mark_done(job_id)
        logger.debug(self.name + ': Exiting...')


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """

    def __init__(self, num_threads, func=None, config=None):
        self.queue = Queue(config)
        self.workers = [Worker(self.queue, func) for _ in range(num_threads)]

    def join(self):
        for worker in self.workers:
            worker.should_exit = True
            worker.join()


def build_job_data(product, kind, organization, counter=1):
    data = None
    if all(arg is not None for arg in [product, kind, organization]):
        data = {
            'product': product,
            'kind': kind,
            'ts': time.time(),
            'organization': organization,
            'counter': counter
        }
    return data
