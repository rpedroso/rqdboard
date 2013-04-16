# coding: utf-8

from gluon.globals import current
from gluon.html import (URL, TABLE, THEAD, TR, TD, TH, A, I,
        SPAN, PRE, XML, DIV)
from gluon.http import HTTP, redirect

from redis import Redis, ResponseError, ConnectionError
from rq import Queue, Worker
from rq import cancel_job, requeue_job
from rq import get_failed_queue
from rq import push_connection, get_current_connection
import times
import datetime


# Borrow from gluon/tools.py
def utc_prettydate(d):
    T = current.T
    if isinstance(d, datetime.datetime):
        dt = times.now() - d
    elif not d:
        return ''
    else:
        return '[invalid date]'
    if dt.days < 0:
        suffix = ' from now'
        dt = -dt
    else:
        suffix = ' ago'
    if dt.days >= 2 * 365:
        return T('%d years' + suffix) % int(dt.days / 365)
    elif dt.days >= 365:
        return T('1 year' + suffix)
    elif dt.days >= 60:
        return T('%d months' + suffix) % int(dt.days / 30)
    elif dt.days > 21:
        return T('1 month' + suffix)
    elif dt.days >= 14:
        return T('%d weeks' + suffix) % int(dt.days / 7)
    elif dt.days >= 7:
        return T('1 week' + suffix)
    elif dt.days > 1:
        return T('%d days' + suffix) % dt.days
    elif dt.days == 1:
        return T('1 day' + suffix)
    elif dt.seconds >= 2 * 60 * 60:
        return T('%d hours' + suffix) % int(dt.seconds / 3600)
    elif dt.seconds >= 60 * 60:
        return T('1 hour' + suffix)
    elif dt.seconds >= 2 * 60:
        return T('%d minutes' + suffix) % int(dt.seconds / 60)
    elif dt.seconds >= 60:
        return T('1 minute' + suffix)
    elif dt.seconds > 1:
        return T('%d seconds' + suffix) % dt.seconds
    elif dt.seconds == 1:
        return T('1 second' + suffix)
    else:
        return T('now')


def queues_table(_class="table table-bordered"):
    T = current.T
    queues = Queue.all()
    table = TABLE(
                THEAD(
                    TR(TH(T('Queue')), TH(T('Jobs')))
                    ),
                    _class=_class)
    if queues:
        for q in queues:
            qlink = A(q.name, _href=URL(args=['overview', q.name]))
            table.append(TR(TD(qlink), TD(q.count)))
    else:
        table.append(TD(T('No queues'), _colspan="2"))
    return table


def worker_table(_class="table table-bordered"):
    T = current.T
    workers = Worker.all()
    table = TABLE(
                THEAD(
                    TR(TH(T('State'), _width="48px"),
                        TH(T('Worker'),
                        TH(T('Queues'))
                        ))
                    ),
                    _class=_class)

    if workers:
        for w in workers:
            state = 'play' if w.state == 'busy' else 'pause'
            icon = I(_class='icon-' + state)
            table.append(TR(TD(icon),
                            TD(w.name),
                            TD(', '.join(w.queue_names()))
                            )
                        )
    else:
        table.append(TD(T('No workers'), _colspan="3"))
    return table


def jobs_table(queue_name, _class="table table-bordered"):
    T = current.T
    queue = Queue(queue_name)

    table = TABLE(
                THEAD(
                    TR(TH(T('Name')),
                        TH(T('Age'),
                        TH(T('Actions'))
                        ))
                    ),
                    _class=_class)

    if queue.jobs:
        for j in queue.jobs:
            icon = I(_class='icon-file')
            span_desc = SPAN(j.description, _class="description")
            div_job_id = DIV(j.id, _class="job_id")

            actions = []

            if j.exc_info:
                span_origin = SPAN(T(' from ') + j.origin, _class="origin")
                span_ended_at = SPAN(
                        utc_prettydate(j.ended_at), _class="end_date")
                pre_exc_info = PRE(j.exc_info, _class="exc_info")
                btn_requeue = A(I(_class="icon-retweet"), T(' Requeue'),
                                    _href=URL(args=['job', j.id,
                                        queue_name, 'requeue']),
                                    _class="btn btn-small",
                                    cid=current.request.cid)
                actions.append(btn_requeue)
            else:
                span_origin = ''
                span_ended_at = ''
                pre_exc_info = ''

            span_created_at = SPAN(utc_prettydate(j.created_at),
                                    _class="created_at")

            btn_cancel = A(I(_class="icon-remove"), T(' Cancel'),
                            _href=URL(args=['job', j.id,
                                        queue_name, 'cancel']),
                            _class="btn btn-small", cid=current.request.cid)
            actions.append(btn_cancel)

            table.append(TR(TD(icon, span_desc,
                                span_origin, div_job_id,
                                span_ended_at, pre_exc_info,
                                ),
                            TD(span_created_at),
                            TD(*actions),
                            )
                        )
    else:
        table.append(TD(T('No jobs'), _colspan="3"))
    return table


def queue_actions(queue_name):
    T = current.T
    btn_requeue_all = A(I(_class="icon-retweet"), T(' Requeue All'),
                    _href=URL(args=['requeue_all']),
                    _style="margin-right: 8px",
                    _class="btn btn-small",
                    )
    btn_compact = A(I(_class="icon-resize-small"), T(' Compact'),
                    _href=URL(args=['compact', queue_name]),
                    _style="margin-right: 8px",
                    _class="btn btn-small",
                    )
    btn_empty = A(I(_class="icon-trash icon-white"), T(' Empty'),
                    _href=URL(args=['empty', queue_name]),
                    _class="btn btn-danger btn-small",
                    )

    return btn_requeue_all + btn_compact + btn_empty


class RQBoard(object):
    def __init__(self, redis_conn=None, poll_interval=2500):
        self._poll_interval = poll_interval
        if get_current_connection() is None:
            if redis_conn is None:
                redis_conn = Redis()
            push_connection(redis_conn)

    def __call__(self):
        func = current.request.args(0) or 'overview'
        args = current.request.args[1:]
        if hasattr(self, func):
            try:
                return getattr(self, func)(*args)
            except ConnectionError:
                return 'Redis down?'
        else:
            raise HTTP(404)

    def overview(self, queue_name=None):
        if queue_name is None:
            # Show the failed queue by default if it contains any jobs
            failed = Queue('failed')
            if not failed.is_empty():
                queue_name = Queue('failed').name
            else:
                queue_name = Queue().name

        return dict(rqdb_queue_name=queue_name,
                    poll_interval=self._poll_interval)

    def queues_table(self):
        return queues_table()

    def workers_table(self):
        return worker_table()

    def job_table(self, queue_name):
        return jobs_table(queue_name)

    def queue_actions_buttons(self, queue_name):
        return queue_actions(queue_name)

    def requeue_all(self):
        fq = get_failed_queue()
        job_ids = fq.job_ids
        count = len(job_ids)
        for job_id in job_ids:
            requeue_job(job_id)
        redirect(URL())

    def compact(self, queue_name):
        q = Queue(queue_name)
        try:
            q.compact()
        except ResponseError:
            # Somethimes I get ResponseError('no such key")
            # from redis connection
            pass
        if current.request.ajax:
            return ''
        redirect(URL(args=['overview'] + current.request.args[1:]))

    def empty(self, queue_name):
        q = Queue(queue_name)
        q.empty()
        redirect(URL(args=['overview'] + current.request.args[1:]))

    def job(self, job_id, queue_name, action):
        if action == 'cancel':
            cancel_job(job_id)
        elif action == 'requeue':
            requeue_job(job_id)
        else:
            raise HTTP(404)
        if current.request.ajax:
            return jobs_table(queue_name)
        redirect(URL())
