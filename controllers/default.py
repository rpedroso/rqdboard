# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations


def dashboard():
    # You can do this in a controller/function of your choice:
    from plugin_rqdboard import RQBoard
    response.view = 'plugin_rqdboard/index.html'
    board = RQBoard(poll_interval=None)  # poll_interval in ms
                                         # if None, don't poll
    return board()


def index():
    redirect(URL('test_rq'))


def test_rq():
    # do not put rqmsg in <app>/modules
    # put it in your web2py/site-packages or in your python site-packages
    import rqmsg

    if session.job_id is None:
        form = SQLFORM.factory(
                Field('calc_fibonacci', 'integer',
                        requires=IS_INT_IN_RANGE(1, 41),
                        comment='enter a number'
                        ),
                submit_button='Submit to queue'
                )

        if form.process().accepted:
            job = rqmsg.RQMsg().enqueue('event_calc', form.vars.calc_fibonacci)
            if job is None:
                redirect(URL('redis_down'))
            else:
                session.job_id = job.id
                redirect(URL())
    else:
        form = None

    return dict(form=form)


def test_rq_result():
    # do not put rqmsg in <app>/modules
    # put it in your web2py/site-packages or in your python site-packages
    import rqmsg

    try:
        job = rqmsg.RQMsg().get_job(session.job_id)
    except rqmsg.ConnectionError:
        redirect(URL('redis_down'))

    if job is None:
        session.job_id = job = None
    elif job.is_finished:
        session.job_id = None

    return dict(job=job)


def redis_down():
    return 'Redis is down, try again later'
