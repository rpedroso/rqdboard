# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations


def dashboard():
    # You can do this in a controller/function of your choice:
    from plugin_rqdboard import RQBoard
    response.view = 'plugin_rqdboard/index.html'
    # poll_interval in ms. If None, don't poll
    poll_interval = request.vars.poll
    board = RQBoard(poll_interval=poll_interval)
    return board()


def index():
    redirect(URL('test_rq_in_model'))


def test_rq_in_model():
    from rqw import RQW

    if session.job_id is None:
        form = SQLFORM.factory(
                Field('calc_fibonacci', 'integer',
                        requires=IS_INT_IN_RANGE(1, 41),
                        comment='enter a number'
                        ),
                submit_button='Submit to queue'
                )

        if form.process().accepted:
            job = RQW().enqueue(func=slow_fib,
                                    args=(form.vars.calc_fibonacci,))
            #job = RQW().enqueue(func='mail.send',
            #                        args=(['me@example.com'],),
            #                        kwargs=dict(subject='teste')
            #                        )
            if job is None:
                redirect(URL('redis_down'))
            else:
                session.job_id = job.id
                redirect(URL())
    else:
        form = None

    return dict(form=form)


def test_rq_in_model_result():
    from rqw import RQW

    try:
        job = RQW().get_job(session.job_id)
    except rqw.ConnectionError:
        redirect('redis_down')

    if job is None:
        session.job_id = job = None
    elif job.is_finished:
        session.job_id = None

    return dict(job=job)


def test_rq():
    from redis import Redis
    from redis.exceptions import ConnectionError
    from rq import Queue

    if session.job_id is None:
        form = SQLFORM.factory(
                Field('calc_fibonacci', 'integer',
                        requires=IS_INT_IN_RANGE(1, 41),
                        comment='enter a number'
                        ),
                submit_button='Submit to queue'
                )

        if form.process().accepted:
            q = Queue(connection=Redis())
            try:
                job = q.enqueue_call(func='jobs.calc_fibonacci.slow_fib',
                                    args=(form.vars.calc_fibonacci,))
            except ConnectionError:
                redirect(URL('redis_down'))
            else:
                session.job_id = job.id
                redirect(URL())
    else:
        form = None

    return dict(form=form)


def test_rq_result():
    from redis import Redis
    from redis.exceptions import ConnectionError
    from rq.job import Job

    try:
        job = Job.fetch(session.job_id, Redis())
    except ConnectionError:
        job = None

    if job is None:
        session.job_id = job = None
    elif job.is_finished:
        session.job_id = None

    return dict(job=job)


def redis_down():
    return 'Redis is down, try again later'
