rqdboard
========

RQ dashboard plugin for web2py + application example.

## How to use:

Install RQ (https://github.com/nvie/rq)

Start redis

Put this application in web2py applications folder

```console
$ cd <web2py_folder>/applications
$ git clone https://github.com/rpedroso/rqdboard
$ cd <web2py_folder>
$ python applications/rqdboard/rq_worker.py
```

Start web2py

Go to http://localhost:8000/rqdboard

