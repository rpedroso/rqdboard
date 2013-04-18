# coding: utf-8
import logging
import inspect

from redis import Redis
from redis.exceptions import ConnectionError

from rq import Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError
from rq import push_connection, get_current_connection

class RQW(object):
    def __init__(self, name='default', redis_conn=None):
        if get_current_connection() is None:
            if redis_conn is None:
                redis_conn = Redis()
            push_connection(redis_conn)
        self.name = name

    def enqueue(self, func, args=None, kwargs=None,
                    timeout=None, result_ttl=None):
        args = args or ()
        if inspect.ismethod(func):
            raise TypeError(
                'instance methods not supported. You need to pass as string')
        elif inspect.isfunction(func):
            fname = func.__name__
        else:
            fname = func

        from gluon.globals import current
        application = current.request.application

        q = Queue(self.name)
        try:
            return q.enqueue_call(func='modules.rqw.run',
                                    args=(fname, application) + args, kwargs=kwargs)
        except ConnectionError:
            return None

    def get_job(self, job_id):
        try:
            return Job.fetch(job_id)
        except NoSuchJobError:
            return None


def run(fname, application, *args, **kwargs):
    logging.info('\tfunction %r in model', fname)
    import sys
    sys.path.insert(0, '.')
    logging.debug('len(sys.path): %r', len(sys.path))

    from gluon.shell import env
    environment = env(application, import_models=True)

    if fname in environment:
        fn = environment[fname]
    else:
        instance_name, _, attribute = fname.rpartition('.')
        fn = getattr(environment[instance_name], attribute)

    return fn(*args, **kwargs)


